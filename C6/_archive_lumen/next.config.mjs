/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // node:sqlite is a built-in Node module; keep it external so Next does
  // not try to bundle the native binding.
  experimental: {
    serverComponentsExternalPackages: ["node:sqlite"],
  },
  env: {
    NEXT_TELEMETRY_DISABLED: "1",
  },
};

export default nextConfig;
