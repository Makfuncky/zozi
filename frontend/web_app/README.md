# ZOZI Web Frontend (Next.js 15 + React 19)

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The backend API must be running on port 8000 for data to load.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Development server with hot reload |
| `npm run build` | Production build |
| `npm run start` | Serve production build |
| `npm run lint` | ESLint (v10 flat config) |
| `npm run typecheck` | TypeScript type checking |

## Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Backend API base URL |
| `NEXT_PUBLIC_WS_URL` | `ws://127.0.0.1:8000` | WebSocket endpoint |

## Architecture

- `app/` — Next.js App Router pages and layouts
- `src/components/` — Reusable React components
- `src/lib/` — API client, utilities, stores
- `src/types/` — TypeScript type definitions

## Testing

```bash
npx playwright install    # Install browser binaries
npx playwright test       # Run e2e tests (requires backend running)
```

Test credentials are seeded by `backend/db/seed.py` on first startup.
