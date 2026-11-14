import { ApiError } from '../api/client'
export async function submitInventory<T>(
  operation: () => Promise<T>,
  refresh: () => Promise<unknown>,
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.code === 'INVENTORY_VERSION_CONFLICT' || error.status === 0 || error.status >= 500)
    )
      await refresh()
    throw error
  }
}
