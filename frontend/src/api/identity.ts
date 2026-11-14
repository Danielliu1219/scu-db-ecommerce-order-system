import { request, query } from './client'
import type { components } from '../types/api'
export type User = components['schemas']['UserOut']
export type LoginResult = components['schemas']['LoginOut']
export const login = (body: components['schemas']['Login']) =>
  request<LoginResult>('/auth/login', 'POST', body)
export const register = (body: components['schemas']['Register']) =>
  request<User>('/auth/register', 'POST', body)
export const me = () => request<User>('/users/me')
export const profile = (body: components['schemas']['ProfilePatch']) =>
  request<User>('/users/me', 'PATCH', body)
export const password = (body: components['schemas']['PasswordChange']) =>
  request<{ changed: boolean }>('/users/me/password', 'PUT', body)
export const users = (params: Record<string, unknown>) =>
  request<{ items: User[]; total: number; page: number; page_size: number }>(
    '/admin/users' + query(params),
  )
