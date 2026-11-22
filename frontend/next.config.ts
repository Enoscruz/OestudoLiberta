import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Gera .next/standalone com o servidor mínimo — necessário para a imagem Docker.
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
