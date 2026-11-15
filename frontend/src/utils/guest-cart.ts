import { product } from '../api/catalog'
import type { Cart, CartItem } from '../api/cart'
import { ApiError, request } from '../api/client'
import { guestSession } from './runtime'

export const guestCartKey = 'scu-ecommerce:guest-cart:v1'
type Entry = { id: string; product_id: string; quantity: number; selected: boolean }
let writing: Promise<unknown> = Promise.resolve()
function serial<T>(operation: () => Promise<T>): Promise<T> {
  const result = writing.then(operation, operation)
  writing = result.then(
    () => undefined,
    () => undefined,
  )
  return result
}

function entries(): Entry[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(guestCartKey) || '[]')
    if (
      !Array.isArray(value) ||
      value.some(
        (e) =>
          !e ||
          typeof e.id !== 'string' ||
          typeof e.product_id !== 'string' ||
          !Number.isInteger(e.quantity) ||
          e.quantity < 1 ||
          e.quantity > 2147483647 ||
          typeof e.selected !== 'boolean',
      )
    )
      throw Error()
    if (new Set(value.map((e) => e.product_id)).size !== value.length) throw Error()
    return value
  } catch {
    localStorage.removeItem(guestCartKey)
    return []
  }
}
function save(value: Entry[]) {
  localStorage.setItem(guestCartKey, JSON.stringify(value))
  window.dispatchEvent(new Event('guest-cart-changed'))
}
function validQuantity(value: number) {
  if (!Number.isInteger(value) || value < 1 || value > 2147483647)
    throw new ApiError('VALIDATION_ERROR', '数量须为有效正整数', 422)
}
async function validate(id: string, quantity: number) {
  validQuantity(quantity)
  const p = await product(id)
  if (p.status !== 'ON_SHELF') throw new ApiError('PRODUCT_OFF_SHELF', '商品已下架', 409)
  if (quantity > p.available) throw new ApiError('STOCK_INSUFFICIENT', '可售库存不足', 409)
}
export async function guestCart(): Promise<Cart> {
  const items: CartItem[] = await Promise.all(
    entries().map(async (e) => {
      let p
      try {
        p = await product(e.product_id)
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 404) throw error
        return {
          ...e,
          product_name: '商品暂不可用',
          price: '0.00',
          available: 0,
          status: 'OFF_SHELF',
          invalid_reason: 'PRODUCT_NOT_FOUND',
        }
      }
      return {
        ...e,
        product_name: p.name,
        price: p.price,
        available: p.available,
        status: p.status,
        invalid_reason:
          p.status !== 'ON_SHELF'
            ? 'PRODUCT_OFF_SHELF'
            : e.quantity > p.available
              ? 'STOCK_INSUFFICIENT'
              : null,
      }
    }),
  )
  const cents = items
    .filter((i) => i.selected)
    .reduce((sum, i) => sum + BigInt(i.price.replace('.', '')) * BigInt(i.quantity), 0n)
  return {
    id: 'guest-cart',
    items,
    selected_total: `${cents / 100n}.${String(cents % 100n).padStart(2, '0')}`,
  }
}
export function guestAdd(product_id: string, quantity: number) {
  return serial(async () => {
    validQuantity(quantity)
    const list = entries(),
      existing = list.find((i) => i.product_id === product_id)
    const target = (existing?.quantity || 0) + quantity
    await validate(product_id, target)
    if (existing) existing.quantity = target
    else list.push({ id: 'guest-' + product_id, product_id, quantity: target, selected: true })
    save(list)
    const cart = await guestCart()
    return {
      item: cart.items.find((i) => i.product_id === product_id)!,
      selected_total: cart.selected_total,
    }
  })
}
export function guestEdit(
  id: string,
  change: { quantity?: number | null; selected?: boolean | null },
) {
  return serial(async () => {
    const list = entries(),
      item = list.find((i) => i.id === id)
    if (!item) throw new ApiError('RESOURCE_NOT_FOUND', '购物车条目不存在', 404)
    if ((change.quantity !== undefined && change.quantity !== null) || change.selected === true)
      await validate(item.product_id, change.quantity ?? item.quantity)
    if (change.quantity != null) item.quantity = change.quantity
    if (change.selected != null) item.selected = change.selected
    save(list)
    const cart = await guestCart()
    return { item: cart.items.find((i) => i.id === id)!, selected_total: cart.selected_total }
  })
}
export function guestRemove(id: string) {
  return serial(async () => {
    save(entries().filter((i) => i.id !== id))
  })
}
export function resetGuestCart() {
  return serial(async () => {
    save([])
  })
}
export const guestCount = () => entries().reduce((sum, item) => sum + item.quantity, 0)

export function importGuestCart() {
  return serial(async () => {
    if (guestSession()) throw new ApiError('UNAUTHENTICATED', '请先登录再导入', 401)
    const token = sessionStorage.getItem('access_token')
    const failures: { product_id: string; message: string }[] = []
    let imported = 0,
      stopped = false
    for (const item of entries()) {
      try {
        if (sessionStorage.getItem('access_token') !== token)
          throw new ApiError('UNAUTHENTICATED', '登录状态已变化，请重新确认账号', 401)
        // Always use the account endpoint: a failed import must never become a guest add.
        await request('/cart/items', 'POST', {
          product_id: item.product_id,
          quantity: item.quantity,
        })
      } catch (error) {
        failures.push({
          product_id: item.product_id,
          message: error instanceof Error ? error.message : '导入未完成',
        })
        const skippable =
          error instanceof ApiError &&
          [
            'PRODUCT_OFF_SHELF',
            'STOCK_INSUFFICIENT',
            'PRODUCT_NOT_FOUND',
            'QUANTITY_OVERFLOW',
          ].includes(error.code)
        if (!skippable) {
          stopped = true
          break
        }
        continue
      }
      // Persist each confirmed success before sending the next increment.
      save(entries().filter((entry) => entry.id !== item.id))
      imported++
    }
    return { imported, failures, remaining: entries().length, stopped }
  })
}
