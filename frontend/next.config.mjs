/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // RTL/Arabic support is handled at the layout level (dir="rtl" + lang="ar").
  // i18n routing will be added in a later phase.
};

export default nextConfig;
