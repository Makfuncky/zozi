import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
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
