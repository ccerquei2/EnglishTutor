// /english-tutor-lessons/vite.config.ts

import path from "path" // 1. Importe o 'path'
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  // 2. Adicione este bloco 'resolve'
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})