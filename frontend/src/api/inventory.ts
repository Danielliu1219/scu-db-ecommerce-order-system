import { request, query } from './client'
import type { components } from '../types/api'
import type { Page } from './catalog'
export type Inventory = components['schemas']['InventoryOut']
export const inventory = (params: Record<string, unknown>) =>
  request<Page<Inventory>>('/admin/inventory' + query(params))
export const restock = (id: string, body: components['schemas']['Restock']) =>
  request<components['schemas']['InventoryMutation']>(
    `/admin/inventory/${id}/restock`,
    'POST',
    body,
  )
export const count = (id: string, body: components['schemas']['Count']) =>
  request<components['schemas']['InventoryMutation']>(`/admin/inventory/${id}/count`, 'POST', body)
