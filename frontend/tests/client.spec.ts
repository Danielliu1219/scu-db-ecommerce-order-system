import { beforeEach, expect, test, vi } from 'vitest'
import { request } from '../src/api/client'
beforeEach(() => {
  sessionStorage.clear()
  vi.restoreAllMocks()
})
test('preserves string IDs and amounts; unwraps data', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ data: { id: '9007199254740993', amount: '80.00' } })),
      ),
  )
  expect(await request('/x')).toEqual({ id: '9007199254740993', amount: '80.00' })
})
test('204 has no body', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
  expect(await request('/x', 'DELETE')).toBeUndefined()
})
test('401 removes token', async () => {
  sessionStorage.setItem('access_token', 'expired')
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ error: { code: 'UNAUTHENTICATED' } }), { status: 401 }),
      ),
  )
  await expect(request('/x')).rejects.toMatchObject({ code: 'UNAUTHENTICATED' })
  expect(sessionStorage.getItem('access_token')).toBeNull()
})
