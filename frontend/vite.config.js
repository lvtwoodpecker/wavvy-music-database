import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// This configuration sets up a development server on port 5173
// we set up our proxy so that requests to /api are forwarded to our Flask backend

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // this is our Flask backend
        changeOrigin: true,
      }
    }
  }
})
