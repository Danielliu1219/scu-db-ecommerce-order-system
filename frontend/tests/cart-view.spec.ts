import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createPinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import CartView from '../src/views/CartView.vue'
import { useAuth } from '../src/stores/auth'
import { guestCartKey } from '../src/utils/guest-cart'

let wrapper: VueWrapper | undefined
const empty = { id: '1', items: [], selected_total: '0.00' }
const entry = { id: 'guest-1', product_id: '1', quantity: 2, selected: true }
const ok = (data: unknown) => new Response(JSON.stringify({ data }))
beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  window.history.replaceState({}, '', '/cart')
})
afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})
async function render(signedIn: boolean) {
  const pinia = createPinia()
  if (signedIn) {
    sessionStorage.setItem('access_token', 'account-token')
    useAuth(pinia).user = { id: '1', username: 'alice', nickname: '用户', phone: '', role: 'USER' }
  }
  wrapper = mount(CartView, {
    global: {
      plugins: [pinia, ElementPlus],
      stubs: { RouterLink: { template: '<a><slot /></a>' } },
    },
  })
  await flushPromises()
  return wrapper
}

test('signed-in cart stays empty until explicit import, then refreshes and hides the entry', async () => {
  localStorage.setItem(guestCartKey, JSON.stringify([entry]))
  const imported = {
    ...empty,
    items: [
      {
        ...entry,
        id: '22',
        product_name: '导入商品',
        price: '5.00',
        available: 10,
        status: 'ON_SHELF',
        invalid_reason: null,
      },
    ],
    selected_total: '10.00',
  }
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(ok(empty))
    .mockResolvedValueOnce(ok({}))
    .mockResolvedValueOnce(ok(imported))
  vi.stubGlobal('fetch', fetcher)
  const view = await render(true)
  expect(view.text()).toContain('购物车为空')
  expect(fetcher).toHaveBeenCalledTimes(1)
  const button = view.findAll('button').find((b) => b.text() === '导入游客购物车')!
  expect(button.exists()).toBe(true)
  await button.trigger('click')
  await flushPromises()
  expect(view.text()).toContain('导入商品')
  expect(view.get('[role="status"]').text()).toContain('已导入 1 种商品')
  expect(view.findAll('button').some((b) => b.text() === '导入游客购物车')).toBe(false)
  expect(fetcher.mock.calls.map(([url, init]) => [url, init.method])).toEqual([
    ['/api/v1/cart', 'GET'],
    ['/api/v1/cart/items', 'POST'],
    ['/api/v1/cart', 'GET'],
  ])
})

test.each([false, true])(
  'no import button without local entries (signed in: %s)',
  async (signedIn) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(() => Promise.resolve(ok(empty))),
    )
    const view = await render(signedIn)
    expect(view.findAll('button').some((b) => b.text() === '导入游客购物车')).toBe(false)
  },
)

test('partial import shows an aggregate reason, retains failed entries and blocks duplicate clicks', async () => {
  const entries = [entry, { ...entry, id: 'guest-2', product_id: '2' }]
  localStorage.setItem(guestCartKey, JSON.stringify(entries))
  let finish: (response: Response) => void = () => undefined
  const pending = new Promise<Response>((resolve) => {
    finish = resolve
  })
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(ok(empty))
    .mockReturnValueOnce(pending)
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { code: 'STOCK_INSUFFICIENT' } }), { status: 409 }),
    )
    .mockResolvedValueOnce(ok(empty))
  vi.stubGlobal('fetch', fetcher)
  const view = await render(true)
  const button = view.findAll('button').find((b) => b.text() === '导入游客购物车')!
  await button.trigger('click')
  await flushPromises()
  expect(button.attributes('disabled')).toBeDefined()
  await button.trigger('click')
  expect(fetcher).toHaveBeenCalledTimes(2)
  finish(ok({}))
  await flushPromises()
  expect(view.get('[role="status"]').text()).toContain('已导入 1 种商品，游客购物车保留 1 种')
  expect(view.get('[role="status"]').text()).toContain('可售库存不足（1 种）')
  expect(JSON.parse(localStorage.getItem(guestCartKey)!)).toEqual([entries[1]])
  expect(button.attributes('disabled')).toBeUndefined()
  expect(fetcher).toHaveBeenCalledTimes(4)
})

test('expired account cart visibly reloads guest items without an error-only dead end', async () => {
  localStorage.setItem(guestCartKey, JSON.stringify([entry]))
  const errorMessage = vi.spyOn(ElMessage, 'error')
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { code: 'UNAUTHENTICATED' } }), { status: 401 }),
    )
    .mockResolvedValueOnce(
      ok({ id: '1', name: '保留的游客商品', price: '5.00', available: 10, status: 'ON_SHELF' }),
    )
  vi.stubGlobal('fetch', fetcher)
  const view = await render(true)
  expect(view.get('h1').text()).toBe('游客购物车')
  expect(view.text()).toContain('保留的游客商品')
  expect(view.text()).toContain('¥10.00')
  expect(errorMessage).not.toHaveBeenCalled()
  expect(fetcher).toHaveBeenCalledTimes(2)
})
