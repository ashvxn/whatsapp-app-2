import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5177,
    // Allows Vite to respond to the random Pinggy subdomain
    allowedHosts: true,
    // Recommended: force a strict port so it doesn't change on you
    strictPort: true,
    hmr: {
      // Use 'wss' (Secure WebSocket) for the public HTTPS tunnel
      protocol: 'wss',
      // If you have a Pro/Static Pinggy URL, put it here. 
      // Otherwise, Vite will try to infer it.
      clientPort: 443, 
    },
  },
})