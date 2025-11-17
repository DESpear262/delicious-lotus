import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
// Vite configuration for the React frontend.
// In development, we proxy API traffic to the FastAPI backend container
// so that the frontend can call `/api/*` without worrying about ports.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'router': ['react-router-dom'],
          'api': ['axios', 'socket.io-client'],
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: false,
    host: true,
    proxy: {
      // Proxy REST API calls to the FastAPI backend in development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy Socket.IO WebSocket connections (used for generation progress)
      '/socket.io': {
        target: 'http://localhost:8000',
        ws: true,
      },
      // Proxy raw WebSocket connections for generation status
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
