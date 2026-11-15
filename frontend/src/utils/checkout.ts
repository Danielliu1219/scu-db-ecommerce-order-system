import type { Checkout } from '../api/orders'
export type Pending = { payload: Checkout; unknown: boolean }
const key = (user: string) => 'checkout:' + user
export function token() {
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}
export function pending(user: string): Pending | null {
  try {
    const raw = sessionStorage.getItem(key(user))
    if (!raw) return null
    const result = JSON.parse(raw) as Pending
    if (
      !/^[0-9a-f]{32}$/.test(result.payload.checkout_token) ||
      !Array.isArray(result.payload.items)
    )
      throw Error()
    return result
  } catch {
    sessionStorage.removeItem(key(user))
    return null
  }
}
export function savePending(user: string, value: Pending) {
  sessionStorage.setItem(key(user), JSON.stringify(value))
}
export function clearPending(user: string) {
  sessionStorage.removeItem(key(user))
}
export function prepare(user: string, body: Omit<Checkout, 'checkout_token'>): Checkout {
  const old = pending(user)
  if (old?.unknown) return old.payload
  const { checkout_token, ...previous } = old?.payload || {}
  return {
    ...body,
    checkout_token:
      JSON.stringify(previous) === JSON.stringify(body) && checkout_token
        ? checkout_token
        : token(),
  }
}
