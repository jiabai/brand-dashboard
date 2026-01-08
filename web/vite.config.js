import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:8000'
  const useMock = env.VITE_USE_MOCK === 'true' && command === 'serve'

  const config = {
    plugins: [react()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        '@/components': fileURLToPath(new URL('./src/components', import.meta.url)),
        '@/lib': fileURLToPath(new URL('./src/lib', import.meta.url))
      }
    },
    server: {
      port: 3000,
    },
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'antd-vendor': ['antd', '@ant-design/icons'],
            'lucide-vendor': ['lucide-react']
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
