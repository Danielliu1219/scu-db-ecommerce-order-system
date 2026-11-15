import { request } from './client'
import type { components } from '../types/api'
import { guestSession } from '../utils/runtime'
import { guestCart, guestAdd, guestEdit, guestRemove } from '../utils/guest-cart'
export type Cart = components['schemas']['CartOut']
export type CartItem = components['schemas']['CartItemOut']
export const cart = () => (guestSession() ? guestCart() : request<Cart>('/cart'))
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
