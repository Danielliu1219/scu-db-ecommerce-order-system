export const states: Record<string, string> = {
  PENDING: '待支付',
  PAID: '已支付',
  SHIPPED: '已发货',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
  ON_SHELF: '上架',
  OFF_SHELF: '下架',
}
export const formatTime = (value: string | null | undefined) =>
  value ? value.replace('T', ' ').replace('+08:00', '') : '—'
export function dateRange(dates: string[] | null | undefined) {
  if (!dates?.length) return {}
  const end = new Date(dates[1] + 'T00:00:00+08:00')
  end.setUTCDate(end.getUTCDate() + 1)
  const next = new Date(end.getTime() + 8 * 3600000).toISOString().slice(0, 10)
  return { start: dates[0] + 'T00:00:00+08:00', end: next + 'T00:00:00+08:00' }
}
