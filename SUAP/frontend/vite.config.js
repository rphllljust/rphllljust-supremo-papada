import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import vue from '@vitejs/plugin-vue'
import path from 'path'

function resolveBackendOrigin(env) {
  if (env.VITE_BACKEND_ORIGIN) {
    return env.VITE_BACKEND_ORIGIN
  }

  if (env.VITE_API_URL) {
    try {
      return new URL(env.VITE_API_URL).origin
    } catch {
      return 'http://127.0.0.1:8000'
    }
  }

  return 'http://127.0.0.1:8000'
}

function resolvePort(rawPort, fallbackPort) {
  const parsedPort = Number.parseInt(rawPort || '', 10)
  return Number.isNaN(parsedPort) ? fallbackPort : parsedPort
}

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendOrigin = resolveBackendOrigin(env)
  const devHost = env.VITE_HOST || '127.0.0.1'
  const devPort = resolvePort(env.VITE_PORT, 5173)
  const devBasePath = env.VITE_DEV_BASE_PATH || '/'
  const buildBasePath = env.VITE_BUILD_BASE_PATH || '/static/'

  return {
    plugins: [react(), vue()],
    base: command === 'serve' ? devBasePath : buildBasePath,
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: devHost,
      port: devPort,
      strictPort: true,
      proxy: {
        '/api': {
          target: backendOrigin,
          changeOrigin: true,
          secure: false,
        },
        '/media': {
          target: backendOrigin,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: 'dist',
      rollupOptions: {
        input: {
          react: path.resolve(__dirname, 'index.html'),
          vue: path.resolve(__dirname, 'vue.html'),
        },
        output: {
          entryFileNames: (chunk) => `${chunk.name}/assets/index.js`,
          chunkFileNames: (chunk) => {
            const facadeId = chunk.facadeModuleId ?? ''
            const app = facadeId.includes('vue') ? 'vue' : 'react'
            return `${app}/assets/[name]-[hash].js`
          },
          assetFileNames: (assetInfo) => {
            const name = assetInfo.names?.[0] ?? ''
            if (name.endsWith('.css')) {
              return 'assets/[name]-[hash][extname]'
            }
            return 'assets/[name]-[hash][extname]'
          },
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'react-query': ['@tanstack/react-query'],
            'vue-vendor': ['vue'],
          },
        },
      },
    },
  }
})
