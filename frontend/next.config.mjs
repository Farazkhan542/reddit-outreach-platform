/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Local dev without nginx: proxy /api to FastAPI. In Docker, nginx routes /api directly.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${process.env.API_ORIGIN ?? "http://localhost:8000"}/api/:path*` }];
  },
};

export default nextConfig;
