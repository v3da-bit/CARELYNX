import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["192.168.31.177", "localhost"],
  // Docker builds set NEXT_OUTPUT=standalone (apps/web/Dockerfile); local dev/build are unchanged.
  ...(process.env.NEXT_OUTPUT === "standalone" ? { output: "standalone" as const } : {}),
};

export default nextConfig;
