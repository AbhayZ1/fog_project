import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      input: {
        admin: 'admin.html',
        client: 'client.html',
      },
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('chart.js') || id.includes('vue-chartjs')) {
              return 'charts';
            }
            if (id.includes('vue')) {
              return 'vendor';
            }
          }
        }
      }
    }
  }
})
