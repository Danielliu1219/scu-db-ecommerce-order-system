import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { guestCartKey, importGuestCart } from '../src/utils/guest-cart'
import * as cart from '../src/api/cart'

const entry = (id: string, quantity = 1) => ({
  id: 'guest-' + id,
  product_id: id,
  quantity,
  selected: true,
})
const stored = () => JSON.parse(localStorage.getItem(guestCartKey) || '[]')
const ok = (data: unknown = {}) => new Response(JSON.stringify({ data }))
const failure = (code: string, status: number) =>
  new Response(JSON.stringify({ error: { code } }), { status })
beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
})
afterEach(() => vi.unstubAllGlobals())

test('imports sequential increments into the account and removes only confirmed successes', async () => {
  sessionStorage.setItem('access_token', 'account-token')
  localStorage.setItem(guestCartKey, JSON.stringify([entry('1', 2), entry('2', 3)]))
  let serverQuantity = 4
  const fetcher = vi.fn(async (_url: string, init: RequestInit) => {
    const body = JSON.parse(init.body as string)
    if (body.product_id === '1') {
      serverQuantity += body.quantity
      return ok({ item: { quantity: serverQuantity } })
    }
    expect(stored()).toEqual([entry('2', 3)])
    return ok()
  })
  vi.stubGlobal('fetch', fetcher)
  expect(await importGuestCart()).toEqual({
    imported: 2,
    failures: [],
    remaining: 0,
    stopped: false,
  })
  expect(serverQuantity).toBe(6)
  expect(
    fetcher.mock.calls.map(([url, init]) => [url, init.method, JSON.parse(init.body as string)]),
  ).toEqual([
    ['/api/v1/cart/items', 'POST', { product_id: '1', quantity: 2 }],
    ['/api/v1/cart/items', 'POST', { product_id: '2', quantity: 3 }],
  ])
  expect(stored()).toEqual([])
  await importGuestCart()
  expect(fetcher).toHaveBeenCalledTimes(2)
})

test('skips off-shelf, insufficient, deleted and overflowing products while retaining failures', async () => {
  sessionStorage.setItem('access_token', 'account-token')
  const entries = ['1', '2', '3', '4', '5'].map((id) => entry(id))
  localStorage.setItem(guestCartKey, JSON.stringify(entries))
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(failure('PRODUCT_OFF_SHELF', 409))
    .mockResolvedValueOnce(failure('STOCK_INSUFFICIENT', 409))
    .mockResolvedValueOnce(failure('PRODUCT_NOT_FOUND', 404))
    .mockResolvedValueOnce(failure('QUANTITY_OVERFLOW', 422))
    .mockResolvedValueOnce(ok())
  vi.stubGlobal('fetch', fetcher)
  const result = await importGuestCart()
  expect(result).toMatchObject({ imported: 1, remaining: 4, stopped: false })
  expect(result.failures.map((f) => f.product_id)).toEqual(['1', '2', '3', '4'])
  expect(stored()).toEqual(entries.slice(0, 4))
  expect(fetcher).toHaveBeenCalledTimes(5)
})

test('anonymous import cannot write or remove guest entries', async () => {
  localStorage.setItem(guestCartKey, JSON.stringify([entry('1')]))
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  await expect(importGuestCart()).rejects.toMatchObject({ code: 'UNAUTHENTICATED' })
  expect(fetcher).not.toHaveBeenCalled()
  expect(stored()).toEqual([entry('1')])
})

test.each(['expired', 'network', 'unknown-commit'])(
  '%s stops import without replaying increments or losing remaining entries',
  async (mode) => {
    sessionStorage.setItem('access_token', 'account-token')
    localStorage.setItem(guestCartKey, JSON.stringify([entry('1'), entry('2'), entry('3')]))
    const fetcher = vi.fn().mockResolvedValueOnce(ok())
    if (mode === 'network') fetcher.mockRejectedValueOnce(new TypeError('connection lost'))
    else
      fetcher.mockResolvedValueOnce(
        failure(
          mode === 'expired' ? 'UNAUTHENTICATED' : 'TRANSACTION_RETRY_EXHAUSTED',
          mode === 'expired' ? 401 : 503,
        ),
      )
    vi.stubGlobal('fetch', fetcher)
    expect(await importGuestCart()).toMatchObject({ imported: 1, remaining: 2, stopped: true })
    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(stored()).toEqual([entry('2'), entry('3')])
    if (mode === 'expired') expect(sessionStorage.getItem('access_token')).toBeNull()
  },
)

test('cart 401 clears the token then reloads guest products without authorization', async () => {
  sessionStorage.setItem('access_token', 'expired')
  localStorage.setItem(guestCartKey, JSON.stringify([entry('1', 2)]))
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(failure('UNAUTHENTICATED', 401))
    .mockResolvedValueOnce(
      ok({ id: '1', name: '游客商品', price: '12.50', available: 8, status: 'ON_SHELF' }),
    )
  vi.stubGlobal('fetch', fetcher)
  expect(await cart.cart()).toMatchObject({
    id: 'guest-cart',
    selected_total: '25.00',
    items: [{ product_id: '1', quantity: 2 }],
  })
  expect(sessionStorage.getItem('access_token')).toBeNull()
  expect(fetcher.mock.calls.map(([url]) => url)).toEqual(['/api/v1/cart', '/api/v1/products/1'])
  expect(fetcher.mock.calls[1][1].headers).not.toHaveProperty('Authorization')
})

test.each([403, 500])(
  'cart %s errors do not fall back or clear the account token',
  async (status) => {
    sessionStorage.setItem('access_token', 'valid')
    const fetcher = vi.fn().mockResolvedValue(failure('REQUEST_FAILED', status))
    vi.stubGlobal('fetch', fetcher)
    await expect(cart.cart()).rejects.toMatchObject({ status })
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(sessionStorage.getItem('access_token')).toBe('valid')
  },
)

test('a failed guest reload surfaces its error without retrying indefinitely', async () => {
  sessionStorage.setItem('access_token', 'expired')
  localStorage.setItem(guestCartKey, JSON.stringify([entry('1')]))
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(failure('UNAUTHENTICATED', 401))
    .mockRejectedValueOnce(new TypeError('offline'))
  vi.stubGlobal('fetch', fetcher)
  await expect(cart.cart()).rejects.toMatchObject({ code: 'NETWORK_ERROR' })
  expect(fetcher).toHaveBeenCalledTimes(2)
})
