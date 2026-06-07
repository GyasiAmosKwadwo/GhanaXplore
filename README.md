# GhanaXplore

Backend API for **GhanaXplore** — a digital tourism platform for discovering, booking, and managing Ghana's attractions. Built with FastAPI, PostgreSQL, and Redis.

> Domestic tourism first: attraction discovery, time-slot bookings, operator dashboards, and MoMo-ready payment hooks.

---

## Quick start

Get the API running locally in under 5 minutes:

```bash
git clone <your-repo-url>
cd tourism
cp .env.example .env          # review and adjust if needed
make dev-install              # Python deps + pre-commit
make up                       # start Docker services
make migrate                  # apply database migrations
make seed                     # create default admin user
```

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/api/v1/redoc |
| Health check | http://localhost:8000/health |

**Default admin** (created by `make seed`):

| Email | Password |
|-------|----------|
| `admin@example.com` | `Admin@123` |

Run integration tests:

```bash
# Postgres must be running (make up)
TEST_DATABASE_URL="postgresql+asyncpg://app_user:app_pass@localhost:5433/app_db" make test
```

---

## What this project does

GhanaXplore connects three groups:

- **Tourists** — browse approved attractions, book visit slots, save favorites, leave reviews
- **Operators** — list attractions, manage schedules/time slots, confirm bookings, issue QR entry tokens
- **Administrators** — verify operators, approve listings, manage users and audit logs

### Implemented today

- JWT auth with Redis-backed sessions and RBAC (8 roles)
- Tourist and operator profiles
- Attraction CRUD with approval workflow and readiness scores
- Schedules and time slots with **capacity-aware bookings**
- Booking lifecycle: create → update → cancel → operator confirm (QR token)
- Reviews, favorites, notifications, password reset
- Alembic migrations, Docker Compose dev stack, Render deploy config

### Coming next

- Paystack / MoMo payment integration
- Tour packages, guide marketplace, events calendar
- Offline attraction bundles
- Next.js PWA frontend

---

## Tech stack

| Layer | Choice |
|-------|--------|
| API | FastAPI 0.104, Python 3.11 |
| Database | PostgreSQL 15 (SQLAlchemy 2 async + Alembic) |
| Cache / sessions | Redis 7 |
| Background jobs | Celery + Redis (wired, tasks TBD) |
| Auth | JWT, bcrypt, role-based permissions |
| Dev tooling | pytest, black, isort, mypy, pre-commit |

---

## Project structure

```
app/
├── api/v1/endpoints/   # HTTP route handlers (thin — delegate to services)
├── core/               # config, database, security, deps, permissions
├── models/             # SQLAlchemy domain models
├── schemas/            # Pydantic request/response schemas
├── services/           # Business logic (auth, bookings, attractions, …)
├── repositories/       # Data access layer
├── tasks/              # Celery app config
└── main.py             # FastAPI entry point

alembic/                # Database migrations
docker/                 # Dockerfiles, nginx, logstash
scripts/                # init_db, seed_data, seed_permissions
tests/
├── conftest.py         # Fixtures (in-memory Redis, test DB)
└── integration/        # API integration tests
```

---

## Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (recommended for local dev)
- **Make** (optional but convenient)

For running tests outside Docker, you only need Postgres reachable at `localhost:5433` (mapped by Compose).

---

## Environment setup

Copy the example env file and fill in secrets:

```bash
cp .env.example .env
```

Key variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection (`postgresql+asyncpg://…`) |
| `REDIS_URL` | Session store and cache |
| `SECRET_KEY` / `JWT_SECRET_KEY` | App and token signing |
| `API_VERSION` | Route prefix segment (default `v1` → `/api/v1/…`) |
| `PAYSTACK_*` | Payment gateway (optional until payments ship) |
| `CLOUDINARY_*` | Image hosting (recommended for production) |
| `CORS_ORIGINS` | Frontend origin(s), e.g. `http://localhost:3000` |

> **Note:** If `API_VERSION` is set to something other than `v1` (e.g. `v1.0.0`), all routes move to `/api/v1.0.0/…`. Check `/docs` after startup.

---

## Make commands

```bash
make help            # list all commands
make up              # start Docker stack
make down            # stop services
make logs            # tail all logs
make logs-api        # API logs only
make migrate         # alembic upgrade head
make seed            # seed admin + permissions
make test            # run pytest
make coverage        # tests with coverage report
make lint            # black, isort, flake8, mypy
make format          # auto-format code
```

Database helpers:

```bash
make migrate-create MSG="describe your change"   # new Alembic revision
make migrate-rollback                          # downgrade one step
make shell-db                                  # psql into Postgres
```

---

## API overview

All routes are prefixed with `/api/{API_VERSION}` (default `/api/v1`).

### Auth & users

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register tourist or operator |
| `POST` | `/auth/login` | Login → JWT access token |
| `POST` | `/auth/logout` | Invalidate session |
| `POST` | `/password/forgot` | Request reset code |
| `POST` | `/password/reset` | Reset password |
| `GET` | `/users/me` | Current user profile |

### Tourism core

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/attractions` | Public listing (approved only) |
| `POST` | `/attractions` | Create listing (operator) |
| `PATCH` | `/attractions/{id}/approval` | Approve/reject (admin) |
| `GET` | `/schedules` | Attraction schedules |
| `GET` | `/time-slots` | Bookable time slots |
| `POST` | `/bookings` | Create booking |
| `GET` | `/bookings` | Tourist's bookings |
| `GET` | `/bookings/managed` | Operator's bookings |
| `PATCH` | `/bookings/{id}/confirm` | Confirm + issue QR token |
| `PATCH` | `/bookings/{id}/cancel` | Cancel booking |
| `POST` | `/reviews` | Submit review |
| `POST` | `/favorites` | Save attraction |

### Admin

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/users` | List users |
| `PATCH` | `/admin/operators/{id}/verification` | Verify operator |
| `GET` | `/admin/audit-logs` | Audit trail |

Interactive docs: **http://localhost:8000/docs**

### Example: create a booking

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tourist@example.com","password":"Test123!"}' \
  | jq -r '.access_token')

# 2. Book an attraction slot
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "attraction_id": "<uuid>",
    "time_slot_id": "<uuid>",
    "visit_date": "2026-07-01",
    "party_size": 2,
    "total_amount_ghs": "100.00"
  }'
```

---

## User roles

| Role | Purpose |
|------|---------|
| `tourist` | Browse and book attractions |
| `operator` | Manage listings and bookings |
| `guide` | Tour guide marketplace (model ready, API TBD) |
| `community_host` | Community tourism experiences (TBD) |
| `attraction_manager` | Site-level management |
| `government` | Analytics dashboard (TBD) |
| `investor` | Investment listings (TBD) |
| `administrator` | Platform operations |

Permissions are seeded via `scripts/seed_permissions.py` and enforced with `require_permission()` on protected routes.

---

## Database migrations

Always use Alembic — do not rely on `DB_AUTO_CREATE_TABLES` in production.

```bash
# Create a migration after model changes
make migrate-create MSG="add feature x"

# Apply
make migrate

# Check current version
docker compose exec api alembic current
```

Migration chain:

```
ghx_core_0001 → ghx_no2fa_01 → ghx_profiles_01 → ghx_booking_slot_01
```

---

## Testing

```bash
# All tests
make test

# Integration tests only
pytest tests/integration -v

# With coverage
make coverage
```

Tests use:

- **Postgres** at `localhost:5433` (Docker Compose port mapping)
- **In-memory FakeRedis** — no external Redis required for tests
- Override `TEST_DATABASE_URL` for CI or custom setups

```bash
TEST_DATABASE_URL="postgresql+asyncpg://app_user:app_pass@localhost:5433/app_db" \
  pytest tests/integration/test_bookings.py -v
```

---

## Local development (without full Docker stack)

If you prefer running the API directly:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Start only Postgres + Redis
docker compose up -d postgres redis

# Point .env at localhost (Postgres is on host port 5433)
# DATABASE_URL=postgresql+asyncpg://app_user:app_pass@localhost:5433/app_db
# REDIS_URL=redis://:redis_pass@localhost:6379/0

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

---

## Docker services (local)

`docker compose up` starts:

| Service | Port | Needed for MVP? |
|---------|------|-----------------|
| `api` | 8000 | Yes |
| `postgres` | 5433 | Yes |
| `redis` | 6379 | Yes |
| `celery_worker` | — | Later |
| `rabbitmq` | 5672, 15672 | Optional (Redis can broker Celery) |
| `elasticsearch`, `logstash`, `kibana` | 5601, 9200 | Dev/ops only — skip in production |
| `flower` | 5555 | Celery monitoring — optional |
| `nginx` | 80 | Optional locally |

For production, you only need **API + Postgres + Redis**. See `render.yaml` for a lean deploy profile.

---

## Deployment

### Render (recommended for MVP)

The repo includes `render.yaml` with:

- Web service (FastAPI)
- Worker (Celery)
- Managed Postgres
- Redis (Key-Value)

Connect your repo in the [Render dashboard](https://render.com) and deploy from the blueprint.

### Docker production

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Production checklist

- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] `DEBUG=false`, `APP_ENV=production`
- [ ] Configure `CORS_ORIGINS` to your frontend domain
- [ ] Use managed Postgres and Redis (not containers on same host)
- [ ] Store images on Cloudinary (local disk is ephemeral on PaaS)
- [ ] Register Paystack webhook URL for payment callbacks
- [ ] Enable HTTPS (provided by Render/Heroku/nginx)

---

## Security

- JWT access tokens with Redis session validation
- Token blacklisting on logout
- Account lockout after repeated failed logins
- Bcrypt password hashing (12 rounds)
- RBAC with granular permissions per module
- Pydantic input validation on all endpoints
- CORS and trusted-host middleware

Password rules: minimum 8 characters, at least one uppercase letter and one digit.

---

## Troubleshooting

**API returns 401 immediately after login**

Sessions are stored in Redis. Ensure Redis is running and `REDIS_URL` is correct.

**`Invalid host header` in tests or requests**

Add your host to `ALLOWED_HOSTS` or use `localhost` as the request host.

**Migration fails locally**

```bash
# Postgres not reachable — use Docker host port
DATABASE_URL=postgresql+asyncpg://app_user:app_pass@localhost:5433/app_db alembic upgrade head
```

**Tests can't connect to database**

```bash
docker compose ps postgres          # must be healthy
TEST_DATABASE_URL="postgresql+asyncpg://app_user:app_pass@localhost:5433/app_db" pytest -v
```

**Routes 404 but `/health` works**

Check `API_VERSION` in `.env`. Routes live at `/api/{API_VERSION}/…`, not always `/api/v1/…`.

---

## Contributing

```bash
git checkout -b feature/your-feature
make format && make lint && make test
git commit -m "Describe why, not just what"
```

Pre-commit hooks run automatically after `make dev-install`.

---

## Roadmap

**Phase 1 — Core platform** *(in progress)*

- [x] Auth, RBAC, profiles
- [x] Attractions, schedules, time slots
- [x] Capacity-aware bookings + QR confirmation
- [ ] Paystack / MoMo payments
- [ ] Email and SMS notifications

**Phase 2 — MVP launch**

- [ ] Next.js PWA frontend
- [ ] Tour packages API
- [ ] Operator analytics dashboard
- [ ] Offline attraction bundles

**Phase 3 — Scale**

- [ ] Guide marketplace
- [ ] Community tourism module
- [ ] Events and cultural calendar
- [ ] Government analytics dashboard
- [ ] ReloM8 accommodation integration

---

## License & contact

University of Ghana — BSc. Information Technology project by **Gyasi Amos Kwadwo**.

Questions: open a GitHub issue or email `gyasiamoskwadwo@gmail.com`.
