import { request } from './client'
import type { components } from '../types/api'
export const simulate = (id: string, simulate_result: 'SUCCESS' | 'FAILURE') =>
  request<components['schemas']['SimulateOut']>(`/orders/${id}/payments/simulate`, 'POST', {
    simulate_result,
  })
export const payment = (id: string, admin = false) =>
  request<components['schemas']['PaymentQuery']>(
    admin ? '/admin/payments?order_id=' + encodeURIComponent(id) : `/orders/${id}/payment`,
  )
