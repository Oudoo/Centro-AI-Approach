/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Surface the backend WS/API endpoints to the client bundle.
  env: {
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws",
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;
