/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 将前端 /api/v1/* 请求代理到后端 FastAPI 服务
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.BACKEND_API_URL || 'http://localhost:8000'}/api/v1/:path*`,
      },
    ];
  },
  // 允许后端域名图片等资源加载
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
      },
    ],
  },
};

module.exports = nextConfig;
