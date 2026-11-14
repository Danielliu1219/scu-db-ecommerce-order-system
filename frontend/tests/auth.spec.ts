import { beforeEach, expect, test, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuth } from '../src/stores/auth'
import * as api from '../src/api/identity'
vi.mock('../src/api/identity', () => ({ me: vi.fn(), login: vi.fn() }))
beforeEach(() => {
  sessionStorage.clear()
  setActivePinia(createPinia())
  vi.resetAllMocks()
})
test('restores identity from current server role', async () => {
  sessionStorage.setItem('access_token', 't')
  vi.mocked(api.me).mockResolvedValue({ id: '1', role: 'ADMIN' } as api.User)
  const store = useAuth()
  expect(await store.restore()).toBe(true)
  expect(store.user?.role).toBe('ADMIN')
  store.clear()
  expect(sessionStorage.getItem('access_token')).toBeNull()
})
test('expired credentials are cleared', async () => {
  sessionStorage.setItem('access_token', 't')
  vi.mocked(api.me).mockRejectedValue(new Error('expired'))
  expect(await useAuth().restore()).toBe(false)
  expect(sessionStorage.getItem('access_token')).toBeNull()
})
