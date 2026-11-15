import { ApiError, request } from './client'
import type { components } from '../types/api'
import { guestSession } from '../utils/runtime'
import { guestCart, guestAdd, guestEdit, guestRemove } from '../utils/guest-cart'
export type Cart = components['schemas']['CartOut']
export type CartItem = components['schemas']['CartItemOut']
export async function cart(): Promise<Cart> {
  if (guestSession()) return guestCart()
  try {
    return await request<Cart>('/cart')
  } catch (error) {
    // request clears expired credentials before this one-time, read-only fallback.
    if (error instanceof ApiError && error.status === 401 && guestSession()) return guestCart()
    throw error
  }
}
export const add = (product_id: string, quantity: number) =>
  guestSession()
    ? guestAdd(product_id, quantity)
    : request<components['schemas']['CartMutation']>('/cart/items', 'POST', {
        product_id,
        quantity,
      })
export const edit = (id: string, body: components['schemas']['CartPatch']) =>
  guestSession()
    ? guestEdit(id, body)
    : request<components['schemas']['CartMutation']>('/cart/items/' + id, 'PATCH', body)
export const remove = (id: string) =>
  guestSession() ? guestRemove(id) : request<void>('/cart/items/' + id, 'DELETE')
