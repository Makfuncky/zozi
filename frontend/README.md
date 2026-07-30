# ZOZI Frontend

## Structure

- `web_app/` - Next.js application (main frontend)
- `shared/` - Shared TypeScript package
- `mobile_app/` - React Native / Expo mobile app

## Setup

```bash
cd shared && npm ci --legacy-peer-deps
cd ../web_app && npm ci --legacy-peer-deps
npm run dev
```

## Testing

```bash
cd web_app
npm run test          # Jest unit tests
npm run test:e2e      # Playwright e2e tests
npm run lint          # ESLint
```
