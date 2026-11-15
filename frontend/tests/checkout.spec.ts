import { beforeEach, expect, test } from 'vitest'
import { prepare, pending, savePending, clearPending } from '../src/utils/checkout'
import { dateRange } from '../src/utils/format'
const body = {
  items: [{ cart_item_id: '9007199254740993', quantity: 2 }],
  receiver_name: '同学',
  receiver_phone: '00123',
  receiver_address: '地址',
}
beforeEach(() => sessionStorage.clear())
test('uncertain submission survives reload and keeps original payload', () => {
  const payload = prepare('1', body)
  expect(payload.checkout_token).toMatch(/^[a-f0-9]{32}$/)
  savePending('1', { payload, unknown: true })
  expect(prepare('1', { ...body, receiver_address: '新地址' })).toEqual(payload)
  expect(pending('2')).toBeNull()
  expect(prepare('2', body).checkout_token).not.toEqual(payload.checkout_token)
})
test('known rollback reuses same payload token but edits get a new token', () => {
  const payload = prepare('1', body)
  savePending('1', { payload, unknown: false })
  expect(prepare('1', body).checkout_token).toBe(payload.checkout_token)
  expect(prepare('1', { ...body, receiver_address: '另一个地址' }).checkout_token).not.toBe(
    payload.checkout_token,
  )
  clearPending('1')
  expect(pending('1')).toBeNull()
})
test('inclusive date selection becomes an exclusive next-day boundary', () => {
  expect(dateRange(['2026-11-01', '2026-11-30'])).toEqual({
    start: '2026-11-01T00:00:00+08:00',
    end: '2026-12-01T00:00:00+08:00',
  })
})
