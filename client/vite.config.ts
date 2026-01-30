import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite'
import solid from 'vite-plugin-solid';

export default defineConfig({
  plugins: [solid(), tailwindcss(),],
  server: {
    port: 3000,
  },
  build: {
    target: 'esnext',
  },
});
