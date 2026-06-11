import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }) => {
  const envDir = fileURLToPath(new URL('.', import.meta.url))
  const env = loadEnv(mode, envDir, '')
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:8000'
  const useMock = env.VITE_USE_MOCK === 'true' && command === 'serve'
  const devHost = env.VITE_DEV_HOST || '0.0.0.0'
  const devPort = parseInt(env.VITE_DEV_PORT || '3000', 10)

  const config = {
    plugins: [react()],
    optimizeDeps: {
      // 情感分析路由懒加载且独占引入 @cp949/react-wordcloud；若不预打包，
      // 首次进入该页时 vite 会临时重新优化依赖并触发重载，导致正在加载的
      // 动态模块报 "Failed to fetch dynamically imported module"。预打包以规避。
      include: ['@cp949/react-wordcloud'],
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        '@/components': fileURLToPath(new URL('./src/components', import.meta.url)),
        '@/lib': fileURLToPath(new URL('./src/lib', import.meta.url))
      }
    },
    server: {
      host: devHost,
      port: devPort,
      allowedHosts: ['rushlink.click', 'mc.rushlink.click', 'www.rushlink.click'],
    },
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            const normalizedId = id.replace(/\\/g, '/')
            if (!normalizedId.includes('/node_modules/')) return
            if (normalizedId.includes('/node_modules/react') || normalizedId.includes('/node_modules/react-dom')) {
              return 'react-vendor'
            }
            if (normalizedId.includes('/node_modules/lucide-react')) {
              return 'lucide-vendor'
            }
            if (normalizedId.includes('/node_modules/dayjs')) {
              return 'dayjs-vendor'
            }
          }
        }
      }
    }
  }

  if (!useMock) {
    config.server.proxy = {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        secure: false,
        timeout: 120000,
        proxyTimeout: 120000,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.error('[vite proxy error]', err.message);
          });
        },
      }
    }
  } else {
    config.server.proxy = {}
    config.server.setupMiddlewares = (middlewares) => {
      middlewares.use('/api/task/current', (req, res, next) => {
        if (req.method === 'GET') {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({
            success: true,
            taskName: `Mock任务-${Math.random().toString(36).substring(2, 8)}`
          }))
        } else {
          next()
        }
      })
    }
  }

  return config
})
