# MockInterview AI

AI-powered mock interview assistant for job seekers. Select a target role and difficulty, practice with an AI interviewer via text or voice, and receive a structured scoring report with actionable feedback.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile | Flutter 3.x (iOS + Android) |
| Backend | Python 3.12 + FastAPI |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| AI | OpenAI API (gpt-4o / whisper-1 / tts-1) |

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker & Docker Compose | Docker 20+, Compose v2 | PostgreSQL + Redis containers |
| Python | 3.11+ | Backend runtime |
| Flutter SDK | 3.x (Dart 3.12+) | Mobile app |
| OpenAI API Key | — | AI interview questions, reports, TTS, Whisper |

## Quick Start

### 1. Clone & start infrastructure

```bash
git clone <repo-url> && cd MockInterview_AI
docker-compose up -d postgres redis
```

Wait for health checks to pass (both services report `healthy`).

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env — fill in OPENAI_API_KEY and JWT_SECRET
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify: `curl http://localhost:8000/health` should return `{"status":"ok"}`.

> **Alternative — run backend in Docker:**
> ```bash
> docker-compose up -d backend
> ```
> This builds and starts the backend container with hot reload.

### 3. Mobile

```bash
cd mobile
cp .env.example .env
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter run
```

> **iOS simulator:** change `.env` to `API_BASE_URL=http://localhost:8000/api/v1`
>
> **Android emulator:** keep `.env` as `API_BASE_URL=http://10.0.2.2:8000/api/v1`

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://mockinterview:mockinterview@localhost:5432/mockinterview` | PostgreSQL connection (use `localhost` for local dev, `postgres` for Docker) |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection |
| `JWT_SECRET` | Yes | random 256-bit string | Secret for signing JWT access tokens |
| `JWT_ALGORITHM` | Yes | `HS256` | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Yes | `7` | Refresh token TTL |
| `OPENAI_API_KEY` | Yes | `sk-...` | OpenAI API key |
| `OPENAI_MODEL` | Yes | `gpt-4o` | Chat completion model |
| `OPENAI_WHISPER_MODEL` | No | `whisper-1` | Speech-to-text model |
| `OPENAI_TTS_MODEL` | No | `tts-1` | Text-to-speech model |
| `OPENAI_TTS_VOICE` | No | `alloy` | TTS voice name |
| `OPENAI_TIMEOUT_SECONDS` | No | `60` | Per-request timeout |
| `OPENAI_MAX_RETRIES` | No | `2` | Retry count on OpenAI failures |
| `UPLOAD_DIR` | Yes | `/app/uploads` | Audio upload directory |
| `CORS_ORIGINS` | No | `*` | CORS allowed origins |
| `LOG_LEVEL` | No | `INFO` | Logging level |

### Mobile (`mobile/.env`)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `API_BASE_URL` | Yes | `http://10.0.2.2:8000/api/v1` | Backend API address |

## Testing

### Backend

```bash
cd backend
python -m pytest                  # Run all tests
python -m pytest -v               # Verbose output
python -m ruff check .            # Lint check
```

### Mobile

```bash
cd mobile
flutter analyze                   # Static analysis
```

## Project Structure

```
MockInterview_AI/
├── backend/              # FastAPI backend
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── api/v1/       # API route handlers
│   │   ├── core/         # Config, security, exceptions
│   │   ├── db/           # Database session & engine
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (Auth, Interview, OpenAI, Report)
│   │   └── prompts/      # OpenAI prompt templates
│   ├── tests/            # pytest test suite (236 tests)
│   └── requirements.txt
├── mobile/               # Flutter mobile app
│   └── lib/
│       ├── app/          # App entry, router, theme, DI
│       ├── core/         # Network client, storage, audio service
│       ├── features/     # Feature modules (auth, home, interview, report, history, profile)
│       └── shared/       # Shared models
├── docs/                 # Project documentation
├── docker-compose.yml
└── README.md
```

## Documentation

| Document | Description |
|----------|------------|
| [PRD](./docs/PRD.md) | Product Requirements |
| [Architecture](./docs/ARCHITECTURE.md) | System Architecture |
| [API](./docs/API.md) | API Specification |
| [Database](./docs/DATABASE.md) | Database Design |
| [Tasks](./docs/TASKS.md) | Development Tasks |
| [Coding Standard](./docs/CODING_STANDARD.md) | Coding Conventions |
| [E2E Checklist](./docs/E2E_CHECKLIST.md) | End-to-end smoke test checklist |

## Troubleshooting

### Docker

| Problem | Solution |
|---------|----------|
| `pg_isready` health check fails | Check port 5432 is not in use: `lsof -i :5432` |
| Backend can't connect to postgres | Use `postgres` (not `localhost`) as hostname in `DATABASE_URL` when running in Docker |
| Stale data from previous runs | `docker-compose down -v` to remove volumes, then `docker-compose up -d` |

### Backend

| Problem | Solution |
|---------|----------|
| `alembic upgrade head` fails | Ensure PostgreSQL is running and `DATABASE_URL` is correct |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in a fresh virtual environment |
| OpenAI 502 errors | Check `OPENAI_API_KEY` is valid and has sufficient quota |

### Mobile

| Problem | Solution |
|---------|----------|
| `build_runner` conflicts | Run `dart run build_runner build --delete-conflicting-outputs` |
| API connection refused (Android) | Verify `.env` has `http://10.0.2.2:8000/api/v1` (not `localhost`) |
| API connection refused (iOS) | Verify `.env` has `http://localhost:8000/api/v1` |
| `flutter_secure_storage` crash on iOS | Ensure Keychain access is enabled in `Info.plist` |
