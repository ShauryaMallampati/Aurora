/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    optimizePackageImports: ['recharts', 'lucide-react'],
  },
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
