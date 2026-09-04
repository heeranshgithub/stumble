# frontend

The Stumble app: Next.js (App Router), React 19, TypeScript strict, Tailwind v4, RTK Query.

```bash
pnpm install
pnpm dev -p 3001        # expects the backend on NEXT_PUBLIC_API_BASE_URL (see .env.example)
pnpm lint && pnpm typecheck && pnpm build
```

- `src/app/` routes; every segment has `loading.tsx` and `error.tsx`
- `src/components/stumble/` the design system (tokens live in `src/app/globals.css`)
- `src/components/screens/` one component per screen
- `src/hooks/` `useHoldToTalk` (mic + silence measurement), `useSpeaker` (streaming playback, unlock, fallback)
- `src/store/` the single RTK Query API and its endpoints
- `src/types/api.ts` wire types, mirroring the backend DTOs one for one
- `/kitchen` renders every component on every scene color

See the root README for the product.
