import { demoCategories, demoListing, demoProduct } from './catalog'
import { ApiError } from '../api/client'

export async function demoRequest<T>(path: string, method: string): Promise<T> {
  const url = new URL(path, 'https://demo.invalid')
  if (method === 'GET' && url.pathname === '/categories')
    return demoCategories.map((c) => ({ ...c })) as T
  if (method === 'GET' && url.pathname === '/products') {
    const low = url.searchParams.get('min_price'),
      high = url.searchParams.get('max_price')
    const invalid = [low, high].some(
      (v) => v !== null && (!/^\d+(\.\d{1,2})?$/.test(v) || Number(v) < 0),
    )
    if (invalid || (low && high && Number(low) > Number(high)))
      throw new ApiError('PRICE_RANGE_INVALID', '价格区间不正确', 422)
    return demoListing(url.searchParams) as T
  }
  if (method === 'GET' && /^\/products\/\d+$/.test(url.pathname)) {
    const p = demoProduct(url.pathname.split('/').pop()!)
    if (!p) throw new ApiError('PRODUCT_NOT_FOUND', '商品不存在或已下架', 404)
    return p as T
  }
  throw new ApiError(
    'DEMO_ONLY',
    '展示站仅提供商品与游客购物车体验，账户和交易请在完整系统中测试',
    403,
  )
}
