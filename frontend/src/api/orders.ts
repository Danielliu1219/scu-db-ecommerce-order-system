import { request, query } from './client'
import type { components } from '../types/api'
import type { Page } from './catalog'
export type Order = components['schemas']['OrderOut']
export type Checkout = components['schemas']['Checkout']
export const checkout = (body: Checkout) => request<Order>('/orders', 'POST', body)
export const orders = (params: Record<string, unknown>, admin = false) =>
  request<Page<Order>>((admin ? '/admin/orders' : '/orders') + query(params))
export const order = (id: string, admin = false) =>
  request<Order>((admin ? '/admin/orders/' : '/orders/') + id)
export const cancel = (id: string) => request<Order>(`/orders/${id}/cancel`, 'POST')
export const receipt = (id: string) => request<Order>(`/orders/${id}/confirm-receipt`, 'POST')
export const ship = (id: string) => request<Order>(`/admin/orders/${id}/ship`, 'POST')
