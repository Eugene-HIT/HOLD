import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "placehold.co",
      },
      {
        protocol: "https",
        hostname: "oeqivlgrvlzrtxwsgrzm.supabase.co",
      },
    ],
  },
};

export default nextConfig;
