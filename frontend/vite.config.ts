import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig(({ mode }) => ({
  base: loadEnv(mode, process.cwd(), '').VITE_BASE_PATH || '/',
  plugins: [vue()],
  server: { port: 5173, strictPort: true, proxy: { '/api': 'http://127.0.0.1:8000' } },
}))
