import { defineConfig } from '@playwright/test'
import { existsSync } from 'node:fs'
if (existsSync('../backend/.env')) process.loadEnvFile('../backend/.env')
export default defineConfig({
  testDir: 'tests/e2e',
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: 'http://127.0.0.1:8000',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  reporter: 'list',
})
