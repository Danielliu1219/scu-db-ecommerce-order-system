import { test, expect } from '@playwright/test'

test('public guest flow filters, edits cart, survives refresh and requires no API', async ({
  page,
}) => {
  const errors: string[] = [],
    apiRequests: string[] = []
  page.on('pageerror', (e) => errors.push(e.message))
  page.on('request', (r) => {
    if (r.url().includes('/api/v1')) apiRequests.push(r.url())
  })
  await page.goto('./#/products')
  await expect(page.getByRole('heading', { name: /日常所需/ })).toBeVisible()
  await expect(page.locator('.product-card')).toHaveCount(7)
  await expect(page.locator('.product-photo img').first()).toBeVisible()
  await page.getByRole('button', { name: '文具', exact: true }).click()
  await expect(page.locator('.product-card')).toHaveCount(2)
  await page.getByRole('textbox', { name: '最低价', exact: true }).fill('20')
  await page.getByRole('textbox', { name: '最高价', exact: true }).fill('20')
  await page.getByRole('button', { name: '查询商品', exact: true }).click()
  await expect(page.locator('.product-card')).toHaveCount(1)
  await page.getByRole('button', { name: '加入购物车：日常线圈笔记本', exact: true }).click()
  await page.getByRole('link', { name: '购物车', exact: true }).click()
  await expect(page.getByRole('heading', { name: '游客购物车' })).toBeVisible()
  const amount = page.locator('.page-head .money')
  await expect(amount).toHaveText('¥20.00')
  await page.getByRole('spinbutton').fill('3')
  await page.getByRole('spinbutton').press('Tab')
  await expect(amount).toHaveText('¥60.00')
  await page.reload()
  await expect(amount).toHaveText('¥60.00')
  await page.locator('.el-checkbox').click()
  await expect(amount).toHaveText('¥0.00')
  await page.getByRole('button', { name: '清空游客购物车' }).click()
  await expect(page.getByText('购物车为空，去选购商品吧')).toBeVisible()
  await page.goto('./#/products/7')
  await expect(page.getByRole('button', { name: '暂无库存' })).toBeDisabled()
  await page.goto('./#/login')
  await expect(page.getByRole('heading', { name: '无需注册，即刻体验' })).toBeVisible()
  await expect(page.locator('input[type=password]')).toHaveCount(0)
  expect(errors).toEqual([])
  expect(apiRequests).toEqual([])
  await page.goto('./#/products')
  await expect(page.locator('.product-card')).toHaveCount(7)
  await expect(page.locator('.store-intro-copy')).toHaveCSS('opacity', '1')
  await page.screenshot({
    path: '../assets/preview/implementation/pages-desktop.png',
    fullPage: true,
  })
})

test('mobile layout and nested hash routes work without authentication', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('./#/products/2')
  await expect(page.getByRole('heading', { name: '日常线圈笔记本' })).toBeVisible()
  await page.getByRole('button', { name: '加入购物车', exact: true }).click()
  await page.getByRole('link', { name: '购物车', exact: true }).click()
  await expect(page.getByRole('heading', { name: '游客购物车' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await page.goto('./#/checkout')
  await expect(page).toHaveURL(/#\/login/)
  await page.goto('./#/products')
  await expect(page.locator('.product-card')).toHaveCount(7)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await expect(page.locator('.store-intro-copy')).toHaveCSS('opacity', '1')
  await expect(page.locator('.el-message')).toHaveCount(0)
  await page.screenshot({
    path: '../assets/preview/implementation/pages-mobile.png',
    fullPage: true,
  })
})
