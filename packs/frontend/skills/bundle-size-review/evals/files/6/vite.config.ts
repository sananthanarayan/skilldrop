import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({ filename: 'stats.json', template: 'raw-data', gzipSize: true }),
  ],
  build: {
    target: 'es2020',
  },
})
