import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Next 16 writes AGENTS.md/CLAUDE.md into the app on dev start; the repo root owns those.
  agentRules: false,
};

export default nextConfig;
