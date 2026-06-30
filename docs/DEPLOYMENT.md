# Deployment Guide — set up on a new system (Windows, no Docker)

This guide takes a fresh Windows machine to a running app. Linux notes are at
the end. The app runs as a **single FastAPI process** that serves both the API
and the built React UI on one port — no Docker, no reverse proxy required.

---

## 1. Prerequisites

Install these once on the target machine:

| Tool | Why | Install |
|------|-----|---------|
| **Git** | clone the repo | https://git-scm.com/download/win |
| **uv** | Python 3.14 + all Python deps | `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` |
| **Node.js 18+** | build the React frontend | https://nodejs.org (LTS) |
| **PostgreSQL 14+** | database | https://www.postgresql.org/download/windows/ |

After installing, open a **new** terminal and verify:

```powershell
git --version
uv --version
node --version
psql --version
```

> PostgreSQL must be **running** as a service. During its install, remember the
> password you set for the `postgres` superuser — you'll put it in `.env`.

---

## 2. Get the code

```powershell
git clone https://github.com/mohanjeet-pixel/manual_production_order.git
cd manual_production_order
```

---

## 3. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` and set real values (see the table in [TECHNICAL.md](TECHNICAL.md#configuration)).
At minimum, set the database and JWT values:

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Manual_order
DB_USER=postgres
DB_PASSWORD=<the postgres password you chose at install>

# generate a strong secret:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET=<paste-generated-secret>
```

Fill in `EMAIL` / `PASSWORD` (SMTP app password) and `SAP_*` only if you need
email approvals / SAP posting on this machine.

---

## 4. First run

```powershell
.\start.bat
```

`start.bat` does everything:

1. `uv sync` — creates `.venv` and installs Python deps
2. **Creates the database** `Manual_order` if it doesn't exist, then creates all
   tables/columns and seed data (admin user + approval matrix)
3. `npm install` + `npm run build` — builds the React UI into `frontend/dist`
4. Starts the app

Open **http://localhost:8000** — the UI loads, API docs are at
**http://localhost:8000/docs**.

Default seeded admin login: employee `mohanjeet`, password `Bull@1234`
(**change this immediately** via the Admin screen on a real deployment).

---

## 5. Day-to-day

```powershell
.\start.bat          :: rebuild UI + run (production-style, one process)
```

Development with hot reload (two processes):

```powershell
.\start_fastapi.bat   :: API at http://localhost:8000
.\start_frontend.bat  :: Vite dev server at http://localhost:3000
```

---

## 6. Database notes

- The schema is created automatically on startup (`AUTO_MIGRATE=true`). To do it
  manually / re-run: `uv run python -m backend.scripts.init_db`.
- The bootstrap is **safe to run repeatedly** — it uses `CREATE ... IF NOT
  EXISTS` and never drops data.
- The `DB_USER` needs permission to create databases (the `postgres` superuser
  has it). If you use a restricted user, create the database yourself first:
  `createdb -U postgres Manual_order`, then set `AUTO_MIGRATE` to still apply
  table migrations.

---

## 7. Running it as a real service (optional)

For an always-on local server, set `ENVIRONMENT=production` in `.env` (disables
auto-reload, enforces that `JWT_SECRET` and `DB_PASSWORD` are set) and run
`uv run run.py`. To keep it alive across reboots, wrap it with
[NSSM](https://nssm.cc/) (Windows service) or Task Scheduler "at startup".

---

## 8. Linux / macOS

Same steps; replace the `.bat` files with:

```bash
cp .env.example .env          # then edit it
uv sync
uv run python -m backend.scripts.init_db
( cd frontend && npm install && npm run build )
uv run run.py
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `database setup failed` | Is PostgreSQL running? Are `DB_*` values in `.env` correct? |
| `password authentication failed` | Wrong `DB_PASSWORD` for the `postgres` user. |
| `uv: command not found` | Open a new terminal after installing uv, or re-run the installer. |
| UI shows but API calls fail | Make sure you ran `start.bat` (single process) — in dev mode the Vite server (:3000) proxies to the API (:8000), so both must run. |
| Port 8000 in use | Change `PORT` in `.env`. |
