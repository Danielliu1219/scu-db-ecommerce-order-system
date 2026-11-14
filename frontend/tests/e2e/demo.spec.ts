import { test, expect } from '@playwright/test'

test('two roles: create stock, checkout, pay, ship, receive, cancel and statistics', async ({
  browser,
}) => {
  const password = process.env.ADMIN_PASSWORD
  if (!password) throw new Error('Set ADMIN_PASSWORD and run db.seed first')
  const admin = await browser.newPage(),
    user = await browser.newPage()
  await admin.goto('/login')
  await admin.getByRole('textbox', { name: '用户名', exact: true }).fill('admin')
  await admin.getByLabel('密码', { exact: true }).fill(password)
  await admin.getByRole('button', { name: '登录', exact: true }).click()
  await expect(admin).toHaveURL(/\/admin\//)
  // Create fresh stock through actual admin APIs; credentials remain in browser storage.
  const marker = Date.now().toString()
  const product = await admin.evaluate(async (marker) => {
    const headers = {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + sessionStorage.getItem('access_token'),
    }
    const category = await fetch('/api/v1/admin/categories', {
      method: 'POST',
      headers,
      body: JSON.stringify({ name: '浏览器验收' + marker }),
    }).then((r) => r.json())
    const p = await fetch('/api/v1/admin/products', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        category_id: category.data.id,
        name: '浏览器商品' + marker,
        price: '30.00',
        description: '浏览器验收',
        status: 'ON_SHELF',
      }),
    }).then((r) => r.json())
    await fetch('/api/v1/admin/inventory/' + p.data.id + '/restock', {
      method: 'POST',
      headers,
      body: JSON.stringify({ quantity: 10, expected_version: '0' }),
    })
    return p.data
  }, marker)
  await user.goto('/register')
  const inputs = user.locator('.el-form input')
  await inputs.nth(0).fill('browser_' + marker)
  await inputs.nth(1).fill('BrowserTest2026!')
  await inputs.nth(2).fill('浏览器验收用户')
  await inputs.nth(3).fill('演示-000')
  await user.getByRole('button', { name: '注册账号' }).click()
  await expect(user).toHaveURL(/\/login/)
  await user.getByRole('textbox', { name: '用户名', exact: true }).fill('browser_' + marker)
  await user.getByLabel('密码', { exact: true }).fill('BrowserTest2026!')
  await user.getByRole('button', { name: '登录', exact: true }).click()
  await expect(user).toHaveURL(/\/profile/)
  await user.goto('/products/' + product.id)
  await user.getByRole('button', { name: '加入购物车', exact: true }).click()
  await user.getByRole('link', { name: '购物车', exact: true }).click()
  await user.getByRole('button', { name: '去结算' }).click()
  const receiver = user.locator('.el-form input')
  await receiver.nth(0).fill('验收收件人')
  await receiver.nth(1).fill('00123')
  await user.locator('textarea').fill('四川大学演示地址')
  await user.getByRole('button', { name: '提交订单', exact: true }).click()
  await expect(user).toHaveURL(/\/orders\/\d+/)
  const oid = user.url().split('/').pop()!
  await user.getByRole('button', { name: '模拟失败', exact: true }).click()
  await expect(user.getByRole('button', { name: '模拟成功', exact: true })).toBeVisible()
  await user.getByRole('button', { name: '模拟成功', exact: true }).click()
  await expect(user.getByText('支付编号', { exact: false })).toBeVisible()
  await admin.goto('/admin/orders/' + oid)
  await admin.getByRole('button', { name: '登记发货', exact: true }).click()
  await admin.getByRole('button', { name: '确定', exact: true }).click()
  await expect(admin.locator('.page-head .el-tag')).toHaveText('已发货')
  await user.reload()
  await user.getByRole('button', { name: '确认收货', exact: true }).click()
  await user.getByRole('button', { name: '确定', exact: true }).click()
  await expect(user.locator('.page-head .el-tag')).toHaveText('已完成')
  await admin.goto('/admin/statistics')
  await expect(admin.getByRole('heading', { name: '销售与用户统计' })).toBeVisible()
  await expect(
    admin.locator('.el-table').first().locator('.el-table__body tbody tr'),
  ).not.toHaveCount(0)
  // A second pending order exercises cancellation and single stock restoration.
  const cancelId = await user.evaluate(async (pid) => {
    const headers = {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + sessionStorage.getItem('access_token'),
    }
    const item = await fetch('/api/v1/cart/items', {
      method: 'POST',
      headers,
      body: JSON.stringify({ product_id: pid, quantity: 1 }),
    }).then((r) => r.json())
    const token = Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) =>
      b.toString(16).padStart(2, '0'),
    ).join('')
    const order = await fetch('/api/v1/orders', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        checkout_token: token,
        items: [{ cart_item_id: item.data.item.id, quantity: 1 }],
        receiver_name: '演示',
        receiver_phone: '演示',
        receiver_address: '演示地址',
      }),
    }).then((r) => r.json())
    return order.data.order_id
  }, product.id)
  await user.goto('/orders/' + cancelId)
  await user.getByRole('button', { name: '取消订单', exact: true }).click()
  await user.getByRole('button', { name: '确定', exact: true }).click()
  await expect(user.locator('.page-head .el-tag')).toHaveText('已取消')
  await admin.goto('/admin/inventory')
  await admin.getByPlaceholder('商品编号').fill(product.id)
  await admin.getByRole('button', { name: '查询', exact: true }).click()
  const stockRow = admin.getByRole('row').filter({ hasText: product.name })
  await expect(stockRow.locator('td').nth(2)).toHaveText('9')
  await user.screenshot({ path: '../assets/preview/implementation/user-order.png', fullPage: true })
  await admin.screenshot({
    path: '../assets/preview/implementation/admin-inventory.png',
    fullPage: true,
  })
})

test('lost checkout response survives reload; stale inventory form requires confirmation', async ({
  browser,
}) => {
  const page = await browser.newPage(),
    admin = await browser.newPage(),
    marker = Date.now().toString()
  const login = await admin.request.post('/api/v1/auth/login', {
    data: { username: 'admin', password: process.env.ADMIN_PASSWORD },
  })
  const adminToken = (await login.json()).data.access_token
  const adminHeaders = { Authorization: 'Bearer ' + adminToken }
  const category = await admin.request
    .post('/api/v1/admin/categories', {
      headers: adminHeaders,
      data: { name: '恢复验收' + marker },
    })
    .then((r) => r.json())
  const p = await admin.request
    .post('/api/v1/admin/products', {
      headers: adminHeaders,
      data: {
        category_id: category.data.id,
        name: '恢复商品' + marker,
        price: '20.00',
        description: '恢复验收',
        status: 'ON_SHELF',
      },
    })
    .then((r) => r.json())
  await admin.request.post(`/api/v1/admin/inventory/${p.data.id}/restock`, {
    headers: adminHeaders,
    data: { quantity: 10, expected_version: '0' },
  })
  const username = 'recovery_' + marker,
    password = 'RecoveryTest2026!'
  await page.request.post('/api/v1/auth/register', {
    data: { username, password, nickname: '恢复验收', phone: '演示' },
  })
  const userLogin = await page.request
    .post('/api/v1/auth/login', { data: { username, password } })
    .then((r) => r.json())
  const userToken = userLogin.data.access_token,
    userHeaders = { Authorization: 'Bearer ' + userToken }
  await page.addInitScript((t) => sessionStorage.setItem('access_token', t), userToken)
  await page.request.post('/api/v1/cart/items', {
    headers: userHeaders,
    data: { product_id: p.data.id, quantity: 1 },
  })
  await page.goto('/checkout')
  await page.locator('.el-form input').nth(0).fill('恢复收件人')
  await page.locator('.el-form input').nth(1).fill('00123')
  await page.locator('textarea').fill('恢复地址')
  let committedId = ''
  await page.route('**/api/v1/orders', async (route) => {
    const response = await route.fetch()
    committedId = (await response.json()).data.order_id
    await route.abort('connectionreset')
  })
  await page.getByRole('button', { name: '提交订单', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await page.reload()
  await expect(page.getByRole('button', { name: '确认原提交结果' })).toBeVisible()
  await expect(page.locator('.el-form input').nth(0)).toBeDisabled()
  await page.unroute('**/api/v1/orders')
  await page.getByRole('button', { name: '确认原提交结果' }).click()
  await expect(page).toHaveURL(new RegExp('/orders/' + committedId + '$'))
  const userOrders = await page.request
    .get('/api/v1/orders', { headers: userHeaders })
    .then((r) => r.json())
  expect(userOrders.data.total).toBe(1)
  await admin.addInitScript((t) => sessionStorage.setItem('access_token', t), adminToken)
  await admin.goto('/admin/inventory')
  await admin.getByPlaceholder('商品编号').fill(p.data.id)
  await admin.getByRole('button', { name: '查询', exact: true }).click()
  await expect(admin.getByRole('button', { name: '补货', exact: true })).toHaveCount(1)
  await admin.getByRole('button', { name: '补货', exact: true }).click()
  await admin.request.post(`/api/v1/admin/inventory/${p.data.id}/restock`, {
    headers: adminHeaders,
    data: { quantity: 3, expected_version: '2' },
  })
  await admin.getByRole('button', { name: '确认保存', exact: true }).click()
  await expect(admin.getByRole('dialog')).not.toBeVisible()
  const stock = await admin.request
    .get('/api/v1/admin/inventory?product_id=' + p.data.id, { headers: adminHeaders })
    .then((r) => r.json())
  expect(stock.data.items[0].available).toBe(12)
  expect(stock.data.items[0].version).toBe('3')
})
