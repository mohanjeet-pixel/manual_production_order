# Technical Documentation

Bull Machines — Manual Production Order Management System.

---

## 1. Overview

A web app for raising manual production orders, routing them for email-based
approval against a value-bracket matrix, and posting approved orders to SAP.

- **Backend:** FastAPI (Python 3.14), PostgreSQL, raw SQL via psycopg2.
- **Frontend:** React 18 + Vite single-page app.
- **Auth:** JWT (HS256) bearer tokens.
- **Deployment:** single process, no Docker (see [DEPLOYMENT.md](DEPLOYMENT.md)).

---

## 2. Architecture

Layered backend — each layer only talks to the one below it:

```
HTTP request
   │
   ▼
backend/api/*          Routers — request/response, auth dependency, validation
   │
   ▼
backend/services/*     Business logic (approval rules, batching, mail, SAP)
   │
   ▼
backend/repositories/* Data access — raw SQL, one module per aggregate
   │
   ▼
backend/database/*     Connection pool + SQLAlchemy engine
   │
   ▼
PostgreSQL
```

Cross-cutting:

- `backend/core/` — `config` (settings), `logger`, `security` (JWT), `constants`
- `backend/schemas/` — Pydantic request/response models (`StandardResponse`)
- `backend/dependencies/` — FastAPI dependencies (current-user auth)
- `backend/utils/exceptions.py` — `AppError` → handled into `StandardResponse`
- `backend/etl/` — Excel → product catalog preprocessing/loading
- `backend/scripts/init_db.py` — DB bootstrap (create DB + migrate)

All API responses use a single envelope:

```json
{ "success": true, "message": "...", "data": { ... } }
```

Errors raise `AppError` (or any exception) and are converted to the same shape
by the handlers in `backend/api/main.py`.

---

## 3. Directory layout

```
backend/
  api/            FastAPI routers (one per domain)
  services/       business logic
  repositories/   SQL data access
  database/       connection pool, engine, auth helpers
  core/           config, logger, security, constants
  schemas/        Pydantic models
  dependencies/   auth dependency
  etl/            Excel ingest pipeline
  scripts/        init_db.py, migrate_passwords.py, schema.sql
  utils/          exceptions
frontend/
  src/pages/      Dashboard, NewOrder, BatchOrder, History, Login, admin/, manager/
  src/api.js      fetch wrapper (adds JWT, handles 401)
  vite.config.js  dev server + API proxy
alembic/          migrations (source of truth for schema)
docs/             this documentation
run.py            uvicorn entry point
start.bat         one-command local deploy
```

---

## 4. Request lifecycle

1. Browser calls a relative path (e.g. `POST /orders`) with a `Bearer` token.
2. In production the same FastAPI process serves the UI and API (same origin);
   in dev, Vite (`:3000`) proxies these paths to the API (`:8000`).
3. The router's auth dependency validates the JWT and loads the current user.
4. Router → service (business rules) → repository (SQL) → DB.
5. Result wrapped in `StandardResponse` and returned.

---

## 5. API reference

Interactive docs (always current): **`/docs`** (Swagger) and **`/redoc`**.

### Auth
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/login` | Authenticate, returns JWT |

### Orders
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/orders` | Create a standalone order (sends approval email) |
| GET | `/orders/me` | Current user's orders |

### Batch orders
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/batches` | Create a batch (N lines, one approval email) |
| GET | `/batches/me` | Current user's batches |

### Approval (email-link targets)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/approve/{token}` | Approve a standalone order → posts to SAP |
| GET | `/reject/{token}` | Reject a standalone order |
| GET | `/approve/batch/{token}` | Approve a batch → posts each line to SAP |
| GET | `/reject/batch/{token}` | Reject a batch |
| GET | `/email/...` | HTML approval pages rendered for email clicks |

### Products
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/products/parts` | Parts catalog for the order form |

### Management
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/management/queue` | Pending standalone orders |
| GET | `/management/batches/queue` | Pending batches |
| GET | `/management/history` | Approval history |
| POST | `/management/orders/{token}/re-approve` | Re-approve (re-post to SAP) |

### Admin (`/admin`)
| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/admin/users` | List / create users |
| PUT/DELETE | `/admin/users/{employee_id}` | Update / deactivate user |
| POST | `/admin/users/{employee_id}/reset-password` | Reset a user's password |
| GET/POST | `/admin/matrix` | List / add approval-matrix brackets |
| PUT | `/admin/matrix/{entry_id}` | Update a bracket |
| POST | `/admin/products/upload` | Upload product catalog (Excel) |
| GET | `/admin/audit-logs` | Audit trail |

### Health
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness probe |

---

## 6. Data model

Schema is defined by the Alembic migrations in `alembic/versions/`
(`backend/scripts/schema.sql` is a readable reference dump).

| Table | Purpose |
|-------|---------|
| `users` | Employees; roles `OPERATOR` / `MANAGER` / `ADMIN` |
| `products` | Parts catalog (uploaded from Excel) |
| `approval_matrix` | Value bracket → approver email (L1 ≤ ₹10k, L2 > ₹10k) |
| `manual_order_batches` | Batch header — one approval email per batch |
| `manual_production_orders` | Order lines (standalone or batch members) |
| `sap_order_results` | Raw SAP API response per approved order/line |
| `audit_logs` | Append-only audit trail |
| `plants` / `plant_parts` | Admin plant / plant-part management |

Views: `v_orders_detail`, `v_pending_approvals`, `v_dashboard_summary`.

**Approval matrix (seeded):**

| Level | Range | Approver |
|-------|-------|----------|
| L1 | 0 – 10,000 | ajaydharshan.s@bullmachine.com |
| L2 | 10,001 – ∞ | mohanjeet@bullmachine.com |

### Migrations

| Revision | Description |
|----------|-------------|
| `0001` | Initial schema + views + seed admin/matrix |
| `0002` | Add `remark` columns to orders/batches |
| `0003` | Add `plants` / `plant_parts` tables |

Commands:

```bash
uv run alembic upgrade head          # apply all
uv run alembic current               # show current revision
uv run alembic revision -m "msg"     # new migration (then edit upgrade/downgrade)
uv run alembic downgrade -1          # roll back one
```

---

## 7. Configuration

All settings come from environment variables / `.env`, loaded by
`backend/core/config.py` (pydantic-settings). No secrets are hard-coded.

| Variable | Default | Notes |
|----------|---------|-------|
| `ENVIRONMENT` | `development` | `production` disables reload + enforces secrets |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | uvicorn bind |
| `CORS_ORIGINS` | `*` | comma-separated allowed origins |
| `AUTO_MIGRATE` | `true` | create DB + migrate on startup |
| `DB_HOST/PORT/NAME/USER/PASSWORD` | localhost/5432/Manual_order/postgres/— | PostgreSQL |
| `JWT_SECRET` | — | **required**; long random string |
| `JWT_EXPIRE_MINUTES` | `480` | token lifetime (8h) |
| `SMTP_SERVER/PORT` | gmail/587 | mail transport |
| `EMAIL` / `PASSWORD` | — | sender + SMTP app password |
| `APP_URL` | http://localhost:8000 | base URL embedded in approval emails |
| `SAP_API_URL/USERNAME/PASSWORD` | — | SAP order-post endpoint |

In `production`, the app refuses to start if `JWT_SECRET` or `DB_PASSWORD` is
missing (see `Settings.validate_required`).

---

## 8. Security notes

- Passwords hashed with bcrypt (`passlib`); see `backend/core/security.py`.
- JWT bearer auth on protected routes via the dependency in
  `backend/dependencies/auth.py`.
- Email approval links carry an opaque UUID token; approve/reject are guarded so
  an already-decided order can't be re-decided (status guard).
- `audit_logs` is append-only.
- **Secrets live only in `.env`** (git-ignored). Never commit it. See
  [GIT_WORKFLOW.md](GIT_WORKFLOW.md) for handling the previously-committed `.env`.

---

## 9. Testing

```bash
uv run pytest -q
```

Tests live in `tests/` and use a real PostgreSQL database (SAP HTTP calls are
mocked). They require the schema to exist (run `init_db` first).
