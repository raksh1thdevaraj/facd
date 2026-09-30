import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';
import http from 'node:http';

// Persistent keep-alive agent preventing socket termination during long forensic processing
const keepAliveAgent = new http.Agent({
  keepAlive: true,
  keepAliveMsecs: 65000,
  maxSockets: 100,
  maxFreeSockets: 20,
  timeout: 180000,
});

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        timeout: 180000,
        // @ts-expect-error - http-proxy option
        proxyTimeout: 180000,
        agent: keepAliveAgent,
        headers: {
          Connection: 'keep-alive',
        },
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(503, {
                'Content-Type': 'application/json',
                'Retry-After': '2',
              });
              res.end(
                JSON.stringify({
                  success: false,
                  error:
                    'Backend service is initializing or momentarily unavailable. Automatic retry in progress.',
                  status_code: 503,
                })
              );
            }
          });
        },
      },
      '/verify': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        timeout: 180000,
        // @ts-expect-error - http-proxy option
        proxyTimeout: 180000,
        agent: keepAliveAgent,
        headers: {
          Connection: 'keep-alive',
        },
        bypass: (req) => {
          if (req.headers.accept?.includes('text/html')) {
            return '/index.html';
          }
        },
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(503, {
                'Content-Type': 'application/json',
                'Retry-After': '2',
              });
              res.end(
                JSON.stringify({
                  success: false,
                  error:
                    'Backend service is initializing or momentarily unavailable. Automatic retry in progress.',
                  status_code: 503,
                })
              );
            }
          });
        },
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        timeout: 180000,
        // @ts-expect-error - http-proxy option
        proxyTimeout: 180000,
        agent: keepAliveAgent,
        headers: {
          Connection: 'keep-alive',
        },
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(503, {
                'Content-Type': 'application/json',
                'Retry-After': '2',
              });
              res.end(
                JSON.stringify({
                  status: 'initializing',
                  error: 'Backend service is starting up.',
                  uptime: 0,
                })
              );
            }
          });
        },
      },
    },
  },
  // @ts-expect-error - vitest types augment UserConfig
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/tests/setup.ts'],
  },
});

