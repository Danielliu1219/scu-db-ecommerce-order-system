import { expect, test, vi } from 'vitest'
import { ApiError } from '../src/api/client'
import { submitInventory } from '../src/utils/inventory'
test('version conflict refreshes but never resubmits with a new version', async () => {
  const operation = vi
    .fn()
    .mockRejectedValue(new ApiError('INVENTORY_VERSION_CONFLICT', 'conflict', 409))
  const refresh = vi.fn().mockResolvedValue({ version: '2' })
  await expect(submitInventory(operation, refresh)).rejects.toMatchObject({
    code: 'INVENTORY_VERSION_CONFLICT',
  })
  expect(operation).toHaveBeenCalledTimes(1)
  expect(refresh).toHaveBeenCalledTimes(1)
})
test('lost response refreshes without repeating an increment', async () => {
  const operation = vi.fn().mockRejectedValue(new ApiError('NETWORK_ERROR', 'unknown'))
  const refresh = vi.fn().mockResolvedValue({ available: 20 })
  await expect(submitInventory(operation, refresh)).rejects.toThrow()
  expect(operation).toHaveBeenCalledTimes(1)
  expect(refresh).toHaveBeenCalledTimes(1)
})
