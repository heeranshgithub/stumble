import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Next 16 writes AGENTS.md/CLAUDE.md into the app on dev start; the repo root owns those.
  agentRules: false,
  // Quick tunnels get a new hostname on every restart; without this the dev server serves the
  // HTML to the phone but refuses the /_next/* chunks, so the page never hydrates. Dev only.
  allowedDevOrigins: ["*.trycloudflare.com"],
};

export default nextConfig;
