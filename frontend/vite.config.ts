import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Генерируем уникальный timestamp для каждой сборки
const timestamp = Date.now()

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name]-${timestamp}.js`,
        chunkFileNames: `assets/[name]-${timestamp}.js`,
        assetFileNames: `assets/[name]-${timestamp}.[ext]`
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
