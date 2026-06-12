# MockInterview AI

AI-powered mock interview assistant for job seekers. Select a target role and difficulty, practice with an AI interviewer via text or voice, and receive a structured scoring report with actionable feedback.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile | Flutter 3.x (iOS + Android) |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| AI | OpenAI API (gpt-4o / whisper-1 / tts-1) |

## Prerequisites

- Docker & Docker Compose
- Flutter SDK 3.x
- Python 3.11+
- OpenAI API Key

## Quick Start

### 1. Infrastructure

```bash
docker-compose up -d postgres redis
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env — fill in OPENAI_API_KEY and JWT_SECRET
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Mobile

```bash
cd mobile
cp .env.example .env
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter run
```

## Project Structure

```
MockInterview_AI/
├── backend/          # FastAPI backend
├── mobile/           # Flutter mobile app
├── docs/             # Project documentation
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
