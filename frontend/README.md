# Stumble — frontend

Next.js (App Router), mobile-first PWA. Talks to `../backend` over JSON.

```bash
pnpm install
cp .env.example .env.local     # point NEXT_PUBLIC_API_BASE_URL at the backend
pnpm dev                       # http://localhost:3000
pnpm lint && pnpm typecheck && pnpm build
```

`/kitchen` renders every component on every scene color. It is the audit surface for the design system.
