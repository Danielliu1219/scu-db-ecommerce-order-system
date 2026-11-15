import { beforeEach, expect, test, vi } from 'vitest'
import { demoRequest } from '../src/demo/request'
import { demoProducts, demoProduct } from '../src/demo/catalog'
import {
  guestAdd,
  guestCart,
  guestEdit,
  guestRemove,
  guestCartKey,
  resetGuestCart,
} from '../src/utils/guest-cart'
import { ApiError } from '../src/api/client'
vi.mock('../src/api/catalog', () => ({
  product: vi.fn(async (id: string) => {
    const p = demoProduct(id)
    if (!p) throw new ApiError('PRODUCT_NOT_FOUND', 'missing', 404)
    return p
  }),
}))
beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
})

test('demo catalogue combines category, keyword and inclusive price filters', async () => {
  const result = await demoRequest<{ items: { name: string }[]; total: number }>(
    '/products?category_id=2&keyword=笔&min_price=20&max_price=20',
    'GET',
  )
  expect(result.total).toBe(1)
  expect(result.items[0].name).toContain('笔记本')
  await expect(demoRequest('/products?min_price=30&max_price=20', 'GET')).rejects.toMatchObject({
    code: 'PRICE_RANGE_INVALID',
  })
})
test('demo catalogue refuses all account, trade and admin operations', async () => {
  for (const path of [
    '/auth/register',
    '/orders',
    '/orders/1/payments/simulate',
    '/admin/products',
  ])
    await expect(demoRequest(path, 'POST')).rejects.toMatchObject({ code: 'DEMO_ONLY' })
})
test('guest cart persists, merges, computes decimal amounts and never reserves stock', async () => {
  await guestAdd('2', 2)
  await guestAdd('2', 1)
  expect((await guestCart()).selected_total).toBe('60.00')
  expect(JSON.parse(localStorage.getItem(guestCartKey)!)[0].quantity).toBe(3)
  await guestEdit('guest-2', { selected: false })
  expect((await guestCart()).selected_total).toBe('0.00')
  expect(demoProducts.find((p) => p.id === '2')?.available).toBe(50)
  await guestRemove('guest-2')
  expect((await guestCart()).items).toHaveLength(0)
})
test('concurrent guest additions are serialized and invalid stock leaves cart intact', async () => {
  await Promise.all([guestAdd('1', 1), guestAdd('1', 1)])
  expect((await guestCart()).items[0].quantity).toBe(2)
  await expect(guestAdd('1', 24)).rejects.toMatchObject({ code: 'STOCK_INSUFFICIENT' })
  expect((await guestCart()).items[0].quantity).toBe(2)
  await expect(guestAdd('7', 1)).rejects.toMatchObject({ code: 'STOCK_INSUFFICIENT' })
  await resetGuestCart()
  expect((await guestCart()).items).toHaveLength(0)
})
test('corrupted guest storage recovers and removed products can still be deleted', async () => {
  localStorage.setItem(guestCartKey, '{broken')
  expect((await guestCart()).items).toHaveLength(0)
  localStorage.setItem(
    guestCartKey,
    JSON.stringify([{ id: 'guest-999', product_id: '999', quantity: 1, selected: true }]),
  )
  expect((await guestCart()).items[0].invalid_reason).toBe('PRODUCT_NOT_FOUND')
  await guestRemove('guest-999')
  expect((await guestCart()).items).toHaveLength(0)
})
