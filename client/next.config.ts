import type { NextConfig } from "next";

const nextConfig: NextConfig = {
	async rewrites() {
		// Use the internal Docker service name for server-side rewrites,
		// falling back to localhost for local (non-Docker) development.
		const apiBase =
			process.env.INTERNAL_API_URL ||
			process.env.NEXT_PUBLIC_API_URL ||
			"http://localhost:8000";

		return [
			{
				// Forward /api/* → Django's /api/* (keep the /api/ prefix)
				source: "/api/:path*",
				destination: `${apiBase}/api/:path*`,
			},
		];
	},
};

export default nextConfig;
