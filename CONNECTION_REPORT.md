# Backend ↔ Frontend Connection Report

> Generated: 2026-08-27
> Scope: Full stack connection analysis

---

## 1. Connection Architecture

```
Browser → http://localhost:3000 (Next.js)
        │
        ├── /api/* /auth/* /admin/* /hr/* /__api/* /uploads/*
        │     → Next.js rewrite → http://127.0.0.1:8000/<same path>
        │                                  │
        │                                  ▼
        │                          FastAPI router
        │                                  │
        │                                  ▼
        │                          CORS check → handler
        │
        ├── Bare fetch with absolute http://127.0.0.1:8000
        │     → direct cross-origin → CORS preflight needed
        │
        └── WebSocket → ws://127.0.0.1:8000/ws-chat/... (direct, no proxy)
```

---

## 2. Backend Configuration

### CORS (backend/infrastructure/utils/config.py)
| Key | Value |
|-----|-------|
| `cors_origins` | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://localhost:19006,http://localhost:19000,...` |
| `allow_credentials` | `True` |
| `allow_methods` | `GET,POST,PUT,PATCH,DELETE,OPTIONS` |
| `allow_headers` | `Authorization,Content-Type,X-CSRF-Token,X-Country-Code,X-Requested-With` |

### API Routes (backend/main.py)
- No global API prefix
- Each router carries its own `APIRouter(prefix=...)`
- Health endpoints: `/health`, `/health/deps`, `/health/ready`
- WebSocket: `/ws/user`, `/ws/admin/background-jobs`, `/ws-chat/...`

---

## 3. Frontend Configuration

### Next.js Rewrites (frontend/web_app/next.config.ts)
| Frontend Path | → Backend |
|---|---|
| `/api/:path*` | `${API_URL}/api/:path*` |
| `/auth/:path*` | `${API_URL}/auth/:path*` |
| `/admin/:path*` | `${API_URL}/admin/:path*` |
| `/hr/:path*` | `${API_URL}/hr/:path*` |
| `/__api/:path*` | `${API_URL}/api/:path*` |
| `/uploads/:path*` | `${API_URL}/uploads/:path*` |

### Environment (frontend/web_app/.env.local)
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
AUTH_SECRET=cca34f9ad380fe079fcc6b0190302dbae124aa47cb3c13ab1ba82c0ab04af0a1
```

---

## 4. Identified Problems

### CRITICAL

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | **No StaticFiles mount** | `backend/main.py` | Add `app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")` |
| 2 | **CORS allow_headers missing traceparent** | `backend/middleware/orchestrator.py` | Add `"X-Request-ID", "traceparent", "tracestate"` to `allow_headers` |
| 3 | **WebSocket path mismatch** | `frontend/web_app/src/hooks/useChatWebSocket.ts` | Connects to `/ws/chat/{roomId}` but router is at `/ws-chat/ws/chat/{roomId}` |

### HIGH

| # | Issue | File | Fix |
|---|-------|------|-----|
| 4 | **AUTH_SECRET mismatch risk** | Frontend `.env.local` vs backend `SECRET_KEY` | Add startup assertion or CI check |
| 5 | **Env host inconsistency** | `.env.local` uses `127.0.0.1`, `.env.example` uses `localhost` | Unify to `localhost` |
| 6 | **CORS doesn't expose X-Request-ID** | `backend/middleware/orchestrator.py` | Add `expose_headers=["X-Request-ID"]` |

### MEDIUM

| # | Issue | File | Fix |
|---|-------|------|-----|
| 7 | **No headers() in next.config.ts** | `frontend/web_app/next.config.ts` | Add security headers block for dev |
| 8 | **apiFetch same-origin retry hides CORS issues** | `frontend/web_app/src/lib/api/client.ts` | Add warning log on retry |
| 9 | **Mobile routing relies on Next rewrites** | `frontend/web_app/next.config.ts` | Mobile must call backend directly in production |

---

## 5. How to Run

### Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```powershell
cd frontend/web_app
npm install
npm run dev
```

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
