import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'via.placeholder.com' },
      { protocol: 'https', hostname: 'placehold.co' },
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'https', hostname: 'picsum.photos' },
      { protocol: 'http', hostname: 'localhost' },
      { protocol: 'http', hostname: '127.0.0.1' },
      { protocol: 'https', hostname: '127.0.0.1' },
    ],
    formats: ['image/webp'],
  },
  allowedDevOrigins: [
    "localhost",
    "127.0.0.1",
    "172.19.240.1",
  ],
  async redirects() {
    return [
      {
        source: "/",
        destination: "/products",
        permanent: false,
      },
    ];
  },
  async rewrites() {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
    return [
      {
        source: '/api/auth/:path*',
        destination: `${apiUrl}/api/v1/auth/:path*`,
      },
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: '/admin/:path*',
        destination: `${apiUrl}/admin/:path*`,
      },
      {
        source: '/hr/:path*',
        destination: `${apiUrl}/hr/:path*`,
      },
      {
        source: '/__api/countries',
        destination: `${apiUrl}/api/v1/customer/country/countries`,
      },
      {
        source: '/__api/currency/:path*',
        destination: `${apiUrl}/api/v1/customer/country/currency/:path*`,
      },
      {
        source: '/__api/products/suppliers',
        destination: `${apiUrl}/api/v1/customer/suppliers/products/suppliers`,
      },
      // Module-scoped surfaces. resolveRequestUrl() in src/lib/api/client.ts sends
      // every path that is not /api, /auth or /admin through /__api, so without
      // these rules they all fall into the customer/catalog catch-all below and
      // 404. Rewrites are first-match-wins, so these must stay above it.
      //   backend namespaces: /supplier/*, /api/v1/logistics/logistics/*, /api/v1/employee/*
      { source: '/__api/supplier/:path*', destination: `${apiUrl}/supplier/:path*` },
      { source: '/__api/logistics-partner/:path*', destination: `${apiUrl}/api/v1/logistics/logistics/:path*` },
      { source: '/__api/employee/:path*', destination: `${apiUrl}/api/v1/employee/:path*` },
      { source: '/__api/employees/:path*', destination: `${apiUrl}/api/v1/employee/:path*` },
      { source: '/__api/suppliers/:path*', destination: `${apiUrl}/api/v1/customer/suppliers/:path*` },
      {
        source: '/__api/:path*',
        destination: `${apiUrl}/api/v1/customer/catalog/:path*`,
      },
      {
        source: '/uploads/:path*',
        destination: `${apiUrl}/uploads/:path*`,
      },
    ];
  },
};

export default nextConfig;
