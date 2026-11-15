import { apiBase, demoMode } from '../utils/runtime'

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 0,
    public details?: Record<string, unknown>,
  ) {
    super(message)
  }
}
const messages: Record<string, string> = {
  USERNAME_EXISTS: '用户名已存在',
  INVALID_CREDENTIALS: '用户名或密码错误',
  UNAUTHENTICATED: '登录已失效，请重新登录',
  ROLE_FORBIDDEN: '当前账号没有操作权限',
  VALIDATION_ERROR: '请检查输入内容',
  OLD_PASSWORD_INCORRECT: '原密码不正确',
  PRODUCT_NOT_FOUND: '商品不存在或已下架',
  PRODUCT_OFF_SHELF: '商品已下架',
  STOCK_INSUFFICIENT: '可售库存不足',
  CART_CHANGED: '购物车已变化，请刷新后重新确认',
  CHECKOUT_TOKEN_CONFLICT: '本次结算标识已绑定其他内容',
  EMPTY_CHECKOUT: '请先勾选商品',
  AMOUNT_OVERFLOW: '订单金额超过上限',
  QUANTITY_OVERFLOW: '数量超过上限',
  ORDER_NOT_FOUND: '订单不存在',
  ORDER_STATE_CONFLICT: '当前订单状态不允许该操作',
  CATEGORY_IN_USE: '分类仍有商品',
  CATEGORY_NAME_EXISTS: '分类名称已存在',
  CATEGORY_NOT_FOUND: '分类不存在',
  PRODUCT_IN_USE: '商品仍被购物车或历史订单引用',
  INVENTORY_NOT_ZERO: '商品库存须先核实为零',
  INVENTORY_VERSION_CONFLICT: '库存已变化，请刷新并重新确认',
  PRICE_INVALID: '售价须为正数且最多两位小数',
  PRICE_RANGE_INVALID: '价格区间不正确',
  TIME_RANGE_INVALID: '时间区间不正确',
  AS_OF_INVALID: '截止时间不能晚于当前时间',
  TRANSACTION_RETRY_EXHAUSTED: '操作暂未完成，请核对后重试',
  DATA_INTEGRITY_ERROR: '数据操作未完成，请联系管理员',
}
export function query(params: Record<string, unknown>) {
  const result = new URLSearchParams()
  for (const [key, value] of Object.entries(params))
    if (value !== '' && value !== null && value !== undefined) result.set(key, String(value))
  return result.size ? '?' + result.toString() : ''
}
export async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  if (demoMode) {
    const { demoRequest } = await import('../demo/request')
    return demoRequest<T>(path, method)
  }
  const token = sessionStorage.getItem('access_token')
  let response: globalThis.Response
  try {
    response = await fetch(apiBase + path, {
      method,
      headers: {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError('NETWORK_ERROR', '连接中断，操作结果可能尚待确认')
  }
  if (response.status === 204) return undefined as T
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401) {
      sessionStorage.removeItem('access_token')
      window.dispatchEvent(new Event('auth-expired'))
    }
    const error = payload.error || {}
    throw new ApiError(
      error.code || 'REQUEST_FAILED',
      messages[error.code] || error.message || '请求未完成',
      response.status,
      error.details,
    )
  }
  return payload.data as T
}
