import path from "path";
import type { NextConfig } from "next";

// A stray system-wide NODE_ENV=production makes `next dev` apply the
// production webpack config, which drops the dev CSS loader and breaks
// global CSS compilation (`@tailwind` → "Unexpected character '@'"). Force
// development mode whenever the dev server is launched so the dev server
// works regardless of the inherited environment. Production builds/starts
// are unaffected because they don't pass the "dev" argv.
if (process.argv.includes("dev")) {
  process.env.NODE_ENV = "development";
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    externalDir: true,
    // Tree-shake barrel imports from heavy UI/util libraries so route bundles
    // only pull the icons/components they actually use.
    optimizePackageImports: [
      "framer-motion",
      "lucide-react",
      "react-icons",
      "date-fns",
      "react-chartjs-2",
    ],
  },
  devIndicators: false,
  webpack: (config, { dev }) => {
    // Do NOT disable the webpack cache. The earlier `config.cache = false`
    // forced a full recompile of every route on every request, making the
    // dev server extremely slow (panel routes took 5-90s to load). Next 15
    // defaults to a persistent filesystem cache; `scripts/start-dev.js`
    // clears `.next` once at startup, which prevents the stale-cache
    // corruption that originally motivated disabling it. With the cache
    // on, routes compile once and then reload in ~1-2s.
    // (No `config.cache` assignment — keep Next's default.)
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@shared': path.resolve(__dirname, '../shared/dist'),
      'react-native$': 'react-native-web',
      'react-native-web': path.resolve(__dirname, "node_modules/react-native-web"),
    };
    config.resolve.extensions = [
      '.web.tsx',
      '.web.ts',
      '.web.js',
      '.tsx',
      '.ts',
      '.js',
      ...((config.resolve.extensions as string[]) || []),
    ];
    
    config.resolve.mainFields = ['browser', 'module', 'main'];
    
    config.resolve.modules = [
      ...(config.resolve.modules || []),
      path.resolve(__dirname, 'node_modules'),
    ];

    return config;
  },
  images: {
    // Optimization ON: Next resizes/transcodes remote images (webp) so cards
    // ship appropriately-sized assets instead of full-resolution originals.
    // All product imagery is remote; remotePatterns below whitelist the hosts.
    remotePatterns: [
      { protocol: 'https', hostname: 'via.placeholder.com' },
      { protocol: 'https', hostname: 'placehold.co' },
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'https', hostname: 'picsum.photos' },
      { protocol: 'https', hostname: '**' },
      { protocol: 'http', hostname: 'localhost' },
      { protocol: 'http', hostname: '127.0.0.1' },
      { protocol: 'https', hostname: '127.0.0.1' },
    ],
    formats: ['image/webp'],
  },
  allowedDevOrigins: [
    'localhost',
    '127.0.0.1',
    '172.19.240.1',
  ],
  async rewrites() {
      const apiUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`,
      },
      {
        source: '/auth/:path*',
        destination: `${apiUrl}/auth/:path*`,
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
        source: '/__api/:path*',
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;