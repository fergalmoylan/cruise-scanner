import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    base: '/cruise-scanner/app/',
    build: {
        outDir: '../docs/app',
        emptyOutDir: true,
    },
})
