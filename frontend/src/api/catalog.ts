import { request, query } from './client'
import type { components } from '../types/api'
export type Product = components['schemas']['ProductOut']
export type Category = components['schemas']['CategoryOut']
export type Page<T> = { items: T[]; total: number; page: number; page_size: number }
export const categories = (admin = false) =>
  request<Category[]>(admin ? '/admin/categories' : '/categories')
export const products = (params: Record<string, unknown>, admin = false) =>
  request<Page<Product>>((admin ? '/admin/products' : '/products') + query(params))
export const product = (id: string, admin = false) =>
  request<Product>((admin ? '/admin/products/' : '/products/') + id)
export const saveCategory = (name: string, id?: string) =>
  request<Category>('/admin/categories' + (id ? '/' + id : ''), id ? 'PATCH' : 'POST', { name })
export const deleteCategory = (id: string) => request<void>('/admin/categories/' + id, 'DELETE')
export const createProduct = (body: components['schemas']['ProductCreate']) =>
  request<Product>('/admin/products', 'POST', body)
export const editProduct = (id: string, body: components['schemas']['ProductPatch']) =>
  request<Product>('/admin/products/' + id, 'PATCH', body)
export const productStatus = (id: string, status: Product['status']) =>
  request<Product>('/admin/products/' + id + '/status', 'PUT', { status })
export const deleteProduct = (id: string) => request<void>('/admin/products/' + id, 'DELETE')
