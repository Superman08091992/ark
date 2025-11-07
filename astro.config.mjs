import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import react from '@astrojs/react';
import node from '@astrojs/node';

// https://astro.build/config
export default defineConfig({
  output: 'static',
  integrations: [
    tailwind(),
    react()
  ],
  adapter: node({
    mode: 'standalone'
  }),
  build: {
    assets: '_astro'
  },
  vite: {
    build: {
      rollupOptions: {
        output: {
          assetFileNames: '_astro/[name].[hash][extname]'
        }
      }
    }
  }
});
