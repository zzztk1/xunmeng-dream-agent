import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发时把 /api 与 /assets 代理到后端，避免跨域、登录态(cookie)直接生效
export default defineConfig({
  plugins: [vue()],
  // 构建产物放 /static，避免与后端 /assets(梦境图) 路径冲突
  build: { assetsDir: 'static' },
  server: {
    host: '127.0.0.1',
    port: 3003,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8003', changeOrigin: true },
      '/assets': { target: 'http://127.0.0.1:8003', changeOrigin: true },
    },
  },
})
