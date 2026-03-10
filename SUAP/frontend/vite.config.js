import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ command }) => ({
  plugins: [react(), vue()],
  base: command === 'serve' ? '/' : '/static/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
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
        // Nomes determinísticos para o Django staticfiles
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
}))
