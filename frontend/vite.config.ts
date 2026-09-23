import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'strip-external-links',
      generateBundle(_, bundle) {
        for (const file of Object.values(bundle)) {
          if (file.type === 'chunk') {
            // Replace react error decoder external doc URL with local reference
            file.code = file.code.replace(
              /https:\/\/reactjs\.org\/docs\/error-decoder\.html\?invariant=/g,
              'http://127.0.0.1/error-decoder?invariant='
            );
          }
        }
      },
    },
  ],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
