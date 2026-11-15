import { test, expect } from '@playwright/test'

test('real guest cart stays local through login and imports only on request', async ({
  page,
  request,
}) => {
  const marker = Date.now().toString()
  const username = 'guest_' + marker,
    password = 'GuestBrowser2026!'
  const register = await request.post('/api/v1/auth/register', {
    data: { username, password, nickname: '游客导入验收', phone: '演示' },
  })
  expect(register.status()).toBe(201)
  const login = await request.post('/api/v1/auth/login', {
    data: { username: 'admin', password: process.env.ADMIN_PASSWORD },
  })
  expect(login.ok()).toBe(true)
  const headers = { Authorization: 'Bearer ' + (await login.json()).data.access_token }
  const categoryResponse = await request.post('/api/v1/admin/categories', {
    headers,
    data: { name: '游客验收' + marker },
  })
  expect(categoryResponse.status()).toBe(201)
  const category = (await categoryResponse.json()).data
  const products: { id: string; name: string }[] = []
  for (const suffix of ['A', 'B']) {
    const response = await request.post('/api/v1/admin/products', {
      headers,
      data: {
        category_id: category.id,
        name: '游客商品' + marker + suffix,
        price: '10.00',
        description: '真实系统游客验收',
        status: 'ON_SHELF',
      },
    })
    expect(response.status()).toBe(201)
    const product = (await response.json()).data
    products.push(product)
    const restock = await request.post(`/api/v1/admin/inventory/${product.id}/restock`, {
      headers,
      data: { quantity: 10, expected_version: '0' },
    })
    expect(restock.ok()).toBe(true)
  }

  const cartRequests: { method: string; path: string }[] = []
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('request', (r) => {
    const path = new URL(r.url()).pathname
    if (path.startsWith('/api/v1/cart')) cartRequests.push({ method: r.method(), path })
  })
  await page.goto('/products')
  await expect(page.getByRole('heading', { name: /日常所需/ })).toBeVisible()
  await page.getByPlaceholder('搜索商品名称').fill('游客商品' + marker)
  await page.getByRole('button', { name: '查询商品', exact: true }).click()
  await expect(page.locator('.product-card')).toHaveCount(2)
  await page.getByRole('button', { name: '加入购物车：' + products[0].name, exact: true }).click()
  await expect(page.getByText('已加入游客购物车', { exact: true })).toBeVisible()
  await page.goto('/products/' + products[1].id)
  await expect(page.getByRole('heading', { name: products[1].name, exact: true })).toBeVisible()
  await page.getByRole('button', { name: '加入购物车', exact: true }).click()
  await expect(page.getByText('已加入游客购物车', { exact: true })).toBeVisible()
  await page.getByRole('link', { name: '购物车', exact: true }).click()
  await expect(page.getByRole('heading', { name: '游客购物车', exact: true })).toBeVisible()
  await page.reload()
  const firstRow = page.getByRole('row').filter({ hasText: products[0].name })
  const secondRow = page.getByRole('row').filter({ hasText: products[1].name })
  await expect(firstRow.getByRole('spinbutton')).toHaveValue('1')
  await expect(secondRow.getByRole('spinbutton')).toHaveValue('1')
  await firstRow.getByRole('spinbutton').fill('3')
  await firstRow.getByRole('spinbutton').press('Tab')
  await expect(page.locator('.page-head .money')).toHaveText('¥40.00')
  await secondRow.getByRole('button', { name: '删除', exact: true }).click()
  await expect(secondRow).toHaveCount(0)
  await page.reload()
  await expect(firstRow.getByRole('spinbutton')).toHaveValue('3')
  await expect(page.locator('.page-head .money')).toHaveText('¥30.00')
  expect(cartRequests).toEqual([])
  await expect(page.getByRole('button', { name: '导入游客购物车', exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: '登录后下单', exact: true }).click()
  await expect(page).toHaveURL(/\/login\?next=.*cart/)
  await page.getByRole('textbox', { name: '用户名', exact: true }).fill(username)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page).toHaveURL(/\/cart$/)
  await expect(page.getByText('购物车为空，去选购商品吧', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '导入游客购物车', exact: true })).toBeVisible()
  expect(cartRequests.filter((r) => r.method !== 'GET')).toEqual([])
  const token = await page.evaluate(() => sessionStorage.getItem('access_token'))
  const accountHeaders = { Authorization: 'Bearer ' + token }
  const accountCart = await request.get('/api/v1/cart', { headers: accountHeaders })
  expect(accountCart.ok()).toBe(true)
  expect((await accountCart.json()).data.items).toEqual([])
  const readGuest = () =>
    page.evaluate(() => JSON.parse(localStorage.getItem('scu-ecommerce:guest-cart:v1') || '[]'))
  expect(await readGuest()).toMatchObject([{ product_id: products[0].id, quantity: 3 }])

  await page.getByRole('button', { name: '导入游客购物车', exact: true }).click()
  await expect(firstRow.getByRole('spinbutton')).toHaveValue('3')
  await expect(page.getByRole('status')).toContainText('已导入 1 种商品')
  await expect(page.getByRole('button', { name: '导入游客购物车', exact: true })).toHaveCount(0)
  expect(cartRequests.filter((r) => r.method !== 'GET')).toEqual([
    { method: 'POST', path: '/api/v1/cart/items' },
  ])
  expect(await readGuest()).toEqual([])
  const importedCart = await request.get('/api/v1/cart', { headers: accountHeaders })
  expect((await importedCart.json()).data.items).toMatchObject([
    { product_id: products[0].id, quantity: 3 },
  ])
  const stock = await request.get(`/api/v1/products/${products[0].id}`)
  expect((await stock.json()).data.available).toBe(10)
  expect(errors).toEqual([])
})
