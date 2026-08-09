# Zozi Project — Local Dev Server Run Doc

## How to start the backend

```bash
cd backend
# Activate virtual environment:
# Windows (Git Bash):
source venv/Scripts/activate
# or Windows (CMD/PowerShell):
# .venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

python run_server.py --port 8000
```

The backend starts uvicorn on `0.0.0.0:8000` serving the FastAPI app from `main:app`.
Health check: `curl http://127.0.0.1:8000/health` (returns `{"status":"healthy","version":"1.0.0"}`)

## How to start the frontend

```bash
cd frontend/web_app

# Install dependencies (first time only):
# npx next dev  (will auto-install if needed)

npx next dev --port 3000
```

The frontend starts Next.js on `http://localhost:3000`.
It proxies `/api/:path*` requests to the backend at `http://127.0.0.1:8000/:path*` via middleware.

## Default ports

| Service | Port | URL |
|---------|------|-----|
| Backend (FastAPI) | 8000 | http://127.0.0.1:8000 |
| Frontend (Next.js) | 3000 | http://localhost:3000 |

## Frontend env file

`frontend/web_app/.env.local` — contains API keys, Stripe keys, etc. Must exist for the frontend to run properly.

## Notes

- The backend uses SQLite by default (no external DB needed).
- The frontend dev server may take 20-30s for initial compilation after cache clear.
- Alembic migrations run automatically on backend startup.
- Test users (seeded on first startup):
  - Admin: `admin@zozi.com` / `admin123`
  - Supplier: `supplier@zozi.com` / `supplier123`
  - Customer: `customer@zozi.com` / `customer123`
  - Logistics: `logistics@zozi.com` / `logistics123`
