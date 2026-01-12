import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Adres Backendu jest lokalny dla serwera Vite (czyli Twojego komputera PC)
const BACKEND_TARGET = 'http://127.0.0.1:8000';
const WS_BACKEND_TARGET = 'ws://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    // Wymusza nasłuchiwanie na wszystkich adresach IP w sieci lokalnej
    host: true, 
    port: 5173,
    
    // --- KLUCZOWA KONFIGURACJA PROXY ---
    proxy: {
      // Wszystkie żądania do ścieżki /api/...
      '/api': {
        target: BACKEND_TARGET, // ...zostaną przekierowane na http://127.0.0.1:8000
        changeOrigin: true,    // Wymusza zmianę nagłówka Origin
        // Usuń prefiks /api z żądania przed przekazaniem do FastAPI
        rewrite: (path) => path.replace(/^\/api/, ''), 
      },
      '/ws': {
        target: WS_BACKEND_TARGET,
        ws: true, // <--- TA FLAGA JEST KLUCZOWA!
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ws/, ''), 
      },
    },
    // -----------------------------------
  },
});