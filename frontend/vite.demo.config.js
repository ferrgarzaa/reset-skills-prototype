// Preview build: one self-contained HTML file with the in-browser mock API (no server).
// Used only to share a clickable preview. The real app uses vite.config.js + FastAPI.
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteSingleFile } from 'vite-plugin-singlefile'

export default defineConfig({
  plugins: [vue(), viteSingleFile()],
  define: { 'import.meta.env.VITE_DEMO': JSON.stringify('1') },
  build: { outDir: 'dist-demo' },
})
