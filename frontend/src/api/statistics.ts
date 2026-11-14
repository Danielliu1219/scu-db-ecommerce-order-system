import { request, query } from './client'
import type { components } from '../types/api'
export const monthly = (params: Record<string, unknown>) =>
  request<components['schemas']['MonthlySales'][]>(
    '/admin/statistics/monthly-sales' + query(params),
  )
export const top = (params: Record<string, unknown>) =>
  request<components['schemas']['TopProduct'][]>('/admin/statistics/top-products' + query(params))
export const inactive = (params: Record<string, unknown>) =>
  request<components['schemas']['InactivePage']>('/admin/statistics/inactive-users' + query(params))
