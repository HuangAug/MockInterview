# MockInterview AI

**[中文](#中文) | [English](#english)**

---

## 中文

AI 驱动的模拟面试助手。选择目标岗位和难度，通过文字或语音与 AI 面试官进行练习，获得结构化评分报告与可操作的改进建议。

## English

AI-powered mock interview assistant for job seekers. Select a target role and difficulty, practice with an AI interviewer via text or voice, and receive a structured scoring report with actionable feedback.

---

## Tech Stack / 技术栈

| Layer / 层 | Technology / 技术 |
|------------|-------------------|
| Mobile / 移动端 | Flutter 3.x (iOS + Android) |
| Backend / 后端 | Python 3.12 + FastAPI |
| Database / 数据库 | PostgreSQL 15 |
| Cache / 缓存 | Redis 7 |
| AI | OpenAI API (gpt-4o / whisper-1 / tts-1) |

---

## Prerequisites / 环境准备

| Tool / 工具 | Version / 版本 | Purpose / 用途 |
|-------------|----------------|----------------|
| Docker & Docker Compose | Docker 20+, Compose v2 | PostgreSQL + Redis containers / 数据库与缓存容器 |
| Python | 3.11+ | Backend runtime / 后端运行环境 |
| Flutter SDK | 3.x (Dart 3.12+) | Mobile app / 移动端应用 |
| OpenAI API Key | — | AI interview questions, reports, TTS, Whisper / AI 面试问答、报告、语音合成与转写 |

---

## Quick Start / 快速开始

### 1. Clone & start infrastructure / 克隆并启动基础设施

```bash
git clone <repo-url> && cd MockInterview_AI
docker-compose up -d postgres redis
```

Wait for health checks to pass (both services report `healthy`).
等待健康检查通过（两个服务均显示 `healthy`）。

### 2. Backend / 后端

```bash
cd backend
cp .env.example .env
# Edit .env — fill in OPENAI_API_KEY and JWT_SECRET
# 编辑 .env — 填入 OPENAI_API_KEY 和 JWT_SECRET
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify / 验证: `curl http://localhost:8000/health` should return / 应返回 `{"status":"ok"}`.

> **Alternative — run backend in Docker / 备选方案 — 在 Docker 中运行后端：**
> ```bash
> docker-compose up -d backend
> ```
> This builds and starts the backend container with hot reload.
> 此命令会构建并启动后端容器，支持热重载。

### 3. Mobile / 移动端

```bash
cd mobile
cp .env.example .env
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter run
```

> **iOS simulator / iOS 模拟器：** change `.env` to / 将 `.env` 改为 `API_BASE_URL=http://localhost:8000/api/v1`
>
> **Android emulator / Android 模拟器：** keep `.env` as / 保持 `.env` 为 `API_BASE_URL=http://10.0.2.2:8000/api/v1`

---

## Environment Variables / 环境变量

### Backend (`backend/.env`) / 后端

| Variable / 变量 | Required / 必填 | Example / 示例 | Description / 说明 |
|-----------------|-----------------|----------------|---------------------|
| `DATABASE_URL` | Yes / 是 | `postgresql+asyncpg://mockinterview:mockinterview@localhost:5432/mockinterview` | PostgreSQL connection (use `localhost` for local dev, `postgres` for Docker) / PostgreSQL 连接（本地开发用 `localhost`，Docker 用 `postgres`） |
| `REDIS_URL` | Yes / 是 | `redis://localhost:6379/0` | Redis connection / Redis 连接 |
| `JWT_SECRET` | Yes / 是 | random 256-bit string / 随机 256 位字符串 | Secret for signing JWT access tokens / JWT 访问令牌签名密钥 |
| `JWT_ALGORITHM` | Yes / 是 | `HS256` | JWT algorithm (default: HS256) / JWT 算法（默认：HS256） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes / 是 | `15` | Access token TTL / 访问令牌过期时间（分钟） |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Yes / 是 | `7` | Refresh token TTL / 刷新令牌过期时间（天） |
| `OPENAI_API_KEY` | Yes / 是 | `sk-...` | OpenAI API key / OpenAI API 密钥 |
| `OPENAI_MODEL` | Yes / 是 | `gpt-4o` | Chat completion model / 对话补全模型 |
| `OPENAI_WHISPER_MODEL` | No / 否 | `whisper-1` | Speech-to-text model / 语音转文字模型 |
| `OPENAI_TTS_MODEL` | No / 否 | `tts-1` | Text-to-speech model / 文字转语音模型 |
| `OPENAI_TTS_VOICE` | No / 否 | `alloy` | TTS voice name / TTS 语音名称 |
| `OPENAI_TIMEOUT_SECONDS` | No / 否 | `60` | Per-request timeout / 单次请求超时时间（秒） |
| `OPENAI_MAX_RETRIES` | No / 否 | `2` | Retry count on OpenAI failures / OpenAI 调用失败重试次数 |
| `UPLOAD_DIR` | Yes / 是 | `/app/uploads` | Audio upload directory / 音频上传目录 |
| `CORS_ORIGINS` | No / 否 | `*` | CORS allowed origins / CORS 允许的来源 |
| `LOG_LEVEL` | No / 否 | `INFO` | Logging level / 日志级别 |

### Mobile (`mobile/.env`) / 移动端

| Variable / 变量 | Required / 必填 | Example / 示例 | Description / 说明 |
|-----------------|-----------------|----------------|---------------------|
| `API_BASE_URL` | Yes / 是 | `http://10.0.2.2:8000/api/v1` | Backend API address / 后端 API 地址 |

---

## Testing / 测试

### Backend / 后端

```bash
cd backend
python -m pytest                  # Run all tests / 运行全部测试
python -m pytest -v               # Verbose output / 详细输出
python -m ruff check .            # Lint check / 代码检查
```

### Mobile / 移动端

```bash
cd mobile
flutter analyze                   # Static analysis / 静态分析
```

---

## Project Structure / 项目结构

```
MockInterview_AI/
├── backend/              # FastAPI backend / FastAPI 后端
│   ├── alembic/          # Database migrations / 数据库迁移
│   ├── app/
│   │   ├── api/v1/       # API route handlers / API 路由处理
│   │   ├── core/         # Config, security, exceptions / 配置、安全、异常
│   │   ├── db/           # Database session & engine / 数据库会话与引擎
│   │   ├── models/       # SQLAlchemy ORM models / SQLAlchemy ORM 模型
│   │   ├── schemas/      # Pydantic request/response schemas / Pydantic 请求/响应模型
│   │   ├── services/     # Business logic (Auth, Interview, OpenAI, Report) / 业务逻辑（认证、面试、OpenAI、报告）
│   │   └── prompts/      # OpenAI prompt templates / OpenAI 提示词模板
│   ├── tests/            # pytest test suite (236 tests) / pytest 测试套件（236 项测试）
│   └── requirements.txt
├── mobile/               # Flutter mobile app / Flutter 移动端应用
│   └── lib/
│       ├── app/          # App entry, router, theme, DI / 应用入口、路由、主题、依赖注入
│       ├── core/         # Network client, storage, audio service / 网络客户端、存储、音频服务
│       ├── features/     # Feature modules (auth, home, interview, report, history, profile) / 功能模块（认证、首页、面试、报告、历史、个人）
│       └── shared/       # Shared models / 共享模型
├── docs/                 # Project documentation / 项目文档
├── docker-compose.yml
└── README.md
```

---

## Documentation / 文档

| Document / 文档 | Description / 说明 |
|-----------------|---------------------|
| [PRD](./docs/PRD.md) | Product Requirements / 产品需求文档 |
| [Architecture](./docs/ARCHITECTURE.md) | System Architecture / 系统架构文档 |
| [API](./docs/API.md) | API Specification / API 接口规范 |
| [Database](./docs/DATABASE.md) | Database Design / 数据库设计文档 |
| [Tasks](./docs/TASKS.md) | Development Tasks / 开发任务清单 |
| [Coding Standard](./docs/CODING_STANDARD.md) | Coding Conventions / 编码规范 |
| [E2E Checklist](./docs/E2E_CHECKLIST.md) | End-to-end smoke test checklist / 端到端冒烟测试清单 |

---

## Troubleshooting / 常见问题

### Docker

| Problem / 问题 | Solution / 解决方案 |
|----------------|---------------------|
| `pg_isready` health check fails / 健康检查失败 | Check port 5432 is not in use: `lsof -i :5432` / 检查 5432 端口是否被占用 |
| Backend can't connect to postgres / 后端无法连接 PostgreSQL | Use `postgres` (not `localhost`) as hostname in `DATABASE_URL` when running in Docker / Docker 环境下 `DATABASE_URL` 的主机名应使用 `postgres` 而非 `localhost` |
| Stale data from previous runs / 历史运行残留数据 | `docker-compose down -v` to remove volumes, then `docker-compose up -d` / 执行 `docker-compose down -v` 清除数据卷后重新启动 |

### Backend / 后端

| Problem / 问题 | Solution / 解决方案 |
|----------------|---------------------|
| `alembic upgrade head` fails / 迁移失败 | Ensure PostgreSQL is running and `DATABASE_URL` is correct / 确认 PostgreSQL 正在运行且 `DATABASE_URL` 正确 |
| `ModuleNotFoundError` / 模块未找到 | Run `pip install -r requirements.txt` in a fresh virtual environment / 在全新的虚拟环境中执行 `pip install -r requirements.txt` |
| OpenAI 502 errors / OpenAI 502 错误 | Check `OPENAI_API_KEY` is valid and has sufficient quota / 检查 `OPENAI_API_KEY` 是否有效且有足够配额 |

### Mobile / 移动端

| Problem / 问题 | Solution / 解决方案 |
|----------------|---------------------|
| `build_runner` conflicts / 代码生成冲突 | Run `dart run build_runner build --delete-conflicting-outputs` / 执行此命令并清除冲突输出 |
| API connection refused (Android) / API 连接被拒（Android） | Verify `.env` has `http://10.0.2.2:8000/api/v1` (not `localhost`) / 确认 `.env` 中使用 `10.0.2.2` 而非 `localhost` |
| API connection refused (iOS) / API 连接被拒（iOS） | Verify `.env` has `http://localhost:8000/api/v1` / 确认 `.env` 中使用 `localhost` |
| `flutter_secure_storage` crash on iOS / iOS 上安全存储崩溃 | Ensure Keychain access is enabled in `Info.plist` / 确保 `Info.plist` 中已启用 Keychain 访问 |
