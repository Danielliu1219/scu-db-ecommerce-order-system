import { defineConfig } from '@playwright/test'
import { readFileSync } from 'node:fs'

const basePath =
  readFileSync('.env.pages', 'utf8')
    .match(/^VITE_BASE_PATH=(.+)$/m)?.[1]
    .trim() || '/'
const localURL = 'http://127.0.0.1:4173' + basePath
export default defineConfig({
  testDir: 'tests/e2e',
  testMatch: 'pages.spec.ts',
  workers: 1,
  timeout: 45000,
  use: {
    baseURL: process.env.PAGES_BASE_URL || localURL,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: process.env.PAGES_BASE_URL
    ? undefined
    : { command: 'npm run preview:pages', url: localURL, reuseExistingServer: true },
  reporter: 'list',
})
