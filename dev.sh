#!/usr/bin/env bash
# The whole local stack with phone access: backend, two quick tunnels, frontend pointed at the
# backend tunnel. Run it in its own terminal tab; Ctrl-C stops everything it started.
set -uo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.nvm/versions/node/v24.20.0/bin:$PATH"
LOG=$(mktemp -d /tmp/stumble-dev.XXXX)
trap 'kill $(jobs -p) 2>/dev/null' EXIT INT TERM

(cd backend && uv run uvicorn app.main:app --port 8000 --reload) >"$LOG/backend.log" 2>&1 &
cloudflared tunnel --url http://localhost:8000 >"$LOG/backend-tunnel.log" 2>&1 &
cloudflared tunnel --url http://localhost:3000 >"$LOG/frontend-tunnel.log" 2>&1 &

url() { grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$1" 2>/dev/null | head -1; }
for _ in $(seq 1 60); do
  BE=$(url "$LOG/backend-tunnel.log"); FE=$(url "$LOG/frontend-tunnel.log")
  [ -n "$BE" ] && [ -n "$FE" ] && break; sleep 1
done
[ -z "${BE:-}" ] && { echo "backend tunnel never came up; see $LOG"; exit 1; }

# NEXT_PUBLIC_* is baked in at start, so the frontend starts only once the tunnel URL is known.
sed -i '' "s|^NEXT_PUBLIC_API_BASE_URL=.*|NEXT_PUBLIC_API_BASE_URL=$BE|" frontend/.env.local
(cd frontend && pnpm dev -p 3000) >"$LOG/frontend.log" 2>&1 &

for _ in $(seq 1 60); do
  curl -s -m 2 -o /dev/null http://localhost:8000/health && curl -s -m 3 -o /dev/null http://localhost:3000/ && break; sleep 1
done
printf '\n  phone     %s\n  backend   %s\n  desktop   http://localhost:3000\n  logs      %s\n\nCtrl-C stops everything.\n' "$FE" "$BE" "$LOG"
wait
