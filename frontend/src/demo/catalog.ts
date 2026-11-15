import type { Product, Category, Page } from '../api/catalog'

export const demoCategories: Category[] = [
  { id: '1', name: '数码配件' },
  { id: '2', name: '文具' },
  { id: '3', name: '日用' },
]

const examples = [
  [
    '1',
    '1',
    '轻量头戴耳机',
    '129.00',
    24,
    '有线连接，柔软耳垫。为阅读、学习和日常聆听留一段安静时间。',
  ],
  ['2', '2', '日常线圈笔记本', '20.00', 50, '平整展开，随手记录。让想法、清单和课堂笔记各就其位。'],
  ['3', '1', '无线鼠标', '59.00', 18, '简洁轮廓，轻巧握感。适合书桌与移动办公的日常使用。'],
  [
    '4',
    '3',
    '随行保温杯',
    '39.90',
    32,
    '简约随行杯身，在忙碌的日常里保留一口温度。图片为外观示意。',
  ],
  ['5', '2', '按动中性笔', '5.00', 80, '干净线条，顺手书写。把重要的事认真写下来。'],
  ['6', '3', '白瓷马克杯', '29.00', 16, '温润白瓷与简洁把手，适合一杯咖啡或下午的热茶。'],
  [
    '7',
    '3',
    '桌面阅读灯',
    '89.00',
    0,
    '清晰、克制的桌面轮廓。这是一件用于测试缺货状态的示例商品。',
  ],
] as const

export const demoProducts: Product[] = examples.map(
  ([id, category_id, name, price, available, description]) => ({
    id,
    category_id,
    category_name: demoCategories.find((c) => c.id === category_id)!.name,
    name,
    price,
    available,
    description,
    status: 'ON_SHELF',
    created_at: '2026-11-14T09:00:00+08:00',
    updated_at: '2026-11-14T09:00:00+08:00',
  }),
)

export function demoProduct(id: string): Product | undefined {
  const p = demoProducts.find((p) => p.id === id)
  return p ? { ...p } : undefined
}

export function demoListing(params: URLSearchParams): Page<Product> {
  const low = params.get('min_price'),
    high = params.get('max_price')
  const page = Number(params.get('page') || 1),
    page_size = Number(params.get('page_size') || 20)
  const keyword = (params.get('keyword') || '').trim().toLocaleLowerCase()
  const category = params.get('category_id')
  const items = demoProducts.filter(
    (p) =>
      (!keyword || p.name.toLocaleLowerCase().includes(keyword)) &&
      (!category || p.category_id === category) &&
      (!low || Number(p.price) >= Number(low)) &&
      (!high || Number(p.price) <= Number(high)),
  )
  return {
    items: items.slice((page - 1) * page_size, page * page_size).map((p) => ({ ...p })),
    total: items.length,
    page,
    page_size,
  }
}
