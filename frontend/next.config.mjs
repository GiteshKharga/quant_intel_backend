/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        return [
            {
                source: '/market/:path*',
                destination: 'http://127.0.0.1:8000/market/:path*',
            },
            {
                source: '/analytics/:path*',
                destination: 'http://127.0.0.1:8000/analytics/:path*',
            },
            {
                source: '/trade/:path*',
                destination: 'http://127.0.0.1:8000/trade/:path*',
            },
            {
                source: '/regime',
                destination: 'http://127.0.0.1:8000/regime',
            },
            {
                source: '/health',
                destination: 'http://127.0.0.1:8000/health',
            },
        ];
    },
};

export default nextConfig;
