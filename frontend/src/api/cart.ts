import { request } from './client'
import type { components } from '../types/api'
export type Cart = components['schemas']['CartOut']
export type CartItem = components['schemas']['CartItemOut']
export const cart = () => request<Cart>('/cart')
export const add = (product_id: string, quantity: number) =>
  request<components['schemas']['CartMutation']>('/cart/items', 'POST', { product_id, quantity })
export const edit = (id: string, body: components['schemas']['CartPatch']) =>
  request<components['schemas']['CartMutation']>('/cart/items/' + id, 'PATCH', body)
export const remove = (id: string) => request<void>('/cart/items/' + id, 'DELETE')
