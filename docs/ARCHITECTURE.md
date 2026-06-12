# MockInterview AI — 系统架构文档

> 版本：1.0.0  
> 最后更新：2026-06-12  
> 关联文档：[PRD.md](./PRD.md) | [DATABASE.md](./DATABASE.md) | [API.md](./API.md)

---

## 1. 架构概览

### 1.1 系统上下文

```mermaid
flowchart TB
    subgraph users [Users]
        Candidate[JobSeeker]
    end
    subgraph system [MockInterviewAI]
        MobileApp[FlutterMobileApp]
        Backend[FastAPIBackend]
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Storage[LocalFileStorage]
    end
    subgraph external [ExternalServices]
        OpenAI[OpenAIAPI]
    end
    Candidate --> MobileApp
    MobileApp -->|HTTPS_REST| Backend
    Backend --> DB
    Backend --> Cache
    Backend --> Storage
    Backend -->|HTTPS| OpenAI
```

### 1.2 逻辑分层

```mermaid
flowchart LR
    subgraph client [FlutterApp]
        UI[PresentationLayer]
        BLoC[StateManagement_BLoC]
        Repo[RepositoryLayer]
        APIClient[DioHttpClient]
    end
    subgraph server [FastAPIBackend]
        Router[APIRouter_v1]
        AuthSvc[AuthService]
        UserSvc[UserService]
        InterviewSvc[InterviewService]
        ReportSvc[ReportService]
        AISvc[OpenAIAdapter]
    end
    subgraph storage [Storage]
        PG[(PostgreSQL)]
        Redis[(Redis)]
        Files[uploads/]
    end
    UI --> BLoC --> Repo --> APIClient --> Router
    Router --> AuthSvc & UserSvc & InterviewSvc & ReportSvc
    InterviewSvc --> AISvc
    ReportSvc --> AISvc
    AuthSvc & UserSvc & InterviewSvc & ReportSvc --> PG
    AuthSvc --> Redis
    InterviewSvc --> Files
    AISvc --> OpenAI[OpenAI]
```

---

## 2. Monorepo 目录结构

```
MockInterview_AI/
├── mobile/                              # Flutter 应用
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app/
│   │   │   ├── app.dart                 # MaterialApp 入口
│   │   │   ├── router.dart              # GoRouter 路由
│   │   │   ├── theme.dart               # 主题
│   │   │   └── di.dart                  # 依赖注入 GetIt
│   │   ├── core/
│   │   │   ├── constants/
│   │   │   │   ├── api_constants.dart
│   │   │   │   └── app_constants.dart
│   │   │   ├── network/
│   │   │   │   ├── dio_client.dart
│   │   │   │   ├── auth_interceptor.dart
│   │   │   │   └── api_exception.dart
│   │   │   └── storage/
│   │   │       └── secure_storage.dart
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── data/                # repository, models
│   │   │   │   ├── domain/              # entities (optional)
│   │   │   │   └── presentation/        # bloc, pages, widgets
│   │   │   ├── home/
│   │   │   ├── interview/
│   │   │   ├── report/
│   │   │   ├── history/
│   │   │   └── profile/
│   │   └── shared/
│   │       ├── widgets/
│   │       └── models/                  # 共享 DTO
│   ├── pubspec.yaml
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI app 入口
│   │   ├── api/
│   │   │   ├── deps.py                  # 依赖注入
│   │   │   └── v1/
│   │   │       ├── router.py            # 聚合路由
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── job_roles.py
│   │   │       └── interviews.py
│   │   ├── core/
│   │   │   ├── config.py                # Settings pydantic
│   │   │   ├── security.py              # JWT, bcrypt
│   │   │   ├── exceptions.py            # AppException
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/                      # SQLAlchemy ORM
│   │   │   ├── user.py
│   │   │   ├── refresh_token.py
│   │   │   ├── job_role.py
│   │   │   ├── interview_session.py
│   │   │   ├── interview_message.py
│   │   │   └── interview_report.py
│   │   ├── schemas/                     # Pydantic DTO
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── job_role.py
│   │   │   ├── interview.py
│   │   │   └── report.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── interview_service.py
│   │   │   ├── report_service.py
│   │   │   └── openai_service.py
│   │   └── prompts/
│   │       ├── interview_system_prompt.txt
│   │       ├── interview_first_question_prompt.txt
│   │       ├── interview_next_question_prompt.txt
│   │       └── interview_report_prompt.txt
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── docs/                                # 本文档目录
├── docker-compose.yml
└── README.md
```

---

## 3. 面试会话状态机

### 3.1 会话状态 (interview_sessions.status)

```mermaid
stateDiagram-v2
    [*] --> pending: POST_interviews
    pending --> in_progress: POST_start
    pending --> cancelled: POST_cancel
    in_progress --> completed: POST_complete
    in_progress --> cancelled: POST_cancel_question_count_0
    in_progress --> failed: OpenAI_error_unrecoverable
    completed --> [*]
    cancelled --> [*]
    failed --> [*]
```

| 状态 | 含义 | 允许的操作 |
|------|------|-----------|
| `pending` | 已创建，未开始 | start, cancel |
| `in_progress` | 面试进行中 | submit message, complete, cancel (仅 0 题) |
| `completed` | 正常结束 | 只读：查看 messages, report |
| `cancelled` | 用户取消（通常 0 题） | 只读：查看 messages |
| `failed` | 系统错误 | 只读 |

### 3.2 报告状态 (interview_sessions.report_status)

```mermaid
stateDiagram-v2
    [*] --> pending: session_created
    pending --> generating: POST_complete_and_question_count_gte_1
    generating --> ready: report_saved
    generating --> failed: OpenAI_or_parse_error
    ready --> [*]
    failed --> [*]
```

| 状态 | 含义 |
|------|------|
| `pending` | 未触发报告 |
| `generating` | 后台生成中 |
| `ready` | 报告可读取 |
| `failed` | 生成失败 |

---

## 4. 核心时序

### 4.1 完整面试时序

```mermaid
sequenceDiagram
    participant App as FlutterApp
    participant API as FastAPI
    participant DB as PostgreSQL
    participant AI as OpenAI

    App->>API: POST /interviews
    API->>DB: INSERT session status=pending
    API-->>App: sessionId

    App->>API: POST /interviews/{id}/start
    API->>DB: Load session + job_role
    API->>AI: Generate first question
    AI-->>API: question text
    API->>DB: INSERT message seq=1 role=interviewer
    API->>DB: UPDATE status=in_progress question_count=1
    API-->>App: firstQuestion

    loop Each answer until finished
        App->>API: POST /interviews/{id}/messages {content}
        API->>DB: INSERT message role=candidate
        alt question_count less than max_questions
            API->>AI: Generate next question
            AI-->>API: question or finish signal
            API->>DB: INSERT message role=interviewer
            API->>DB: UPDATE question_count
        else max reached
            API->>DB: Mark isFinished
        end
        API-->>App: nextQuestion or isFinished
    end

    App->>API: POST /interviews/{id}/complete
    API->>DB: UPDATE status=completed report_status=generating
    API->>API: Background task generate report
    API-->>App: completed

    loop Poll every 2s max 60 times
        App->>API: GET /interviews/{id}/report/status
        API-->>App: generating or ready
    end

    App->>API: GET /interviews/{id}/report
    API->>DB: SELECT report
    API-->>App: full report
```

### 4.2 语音转写时序

```mermaid
sequenceDiagram
    participant App as FlutterApp
    participant API as FastAPI
    participant AI as OpenAI

    App->>App: Record audio locally
    App->>API: POST /interviews/{id}/transcribe multipart audio
    API->>AI: whisper-1 transcribe language=zh
    AI-->>API: text
    API-->>App: {text}
    App->>App: Show editable text
    App->>API: POST /interviews/{id}/messages {content}
```

### 4.3 Token 刷新时序

```mermaid
sequenceDiagram
    participant App as FlutterApp
    participant API as FastAPI
    participant Redis as Redis

    App->>API: Request with expired access token
    API-->>App: 401
    App->>API: POST /auth/refresh {refreshToken}
    API->>API: Verify refresh hash in DB
    API->>Redis: Blacklist old refresh (optional TTL)
    API->>API: Issue new token pair rotation
    API-->>App: new tokens
    App->>API: Retry original request
```

---

## 5. OpenAI 集成

### 5.1 模型配置

| 用途 | 模型 | 参数 |
|------|------|------|
| 首题生成 | gpt-4o | temperature=0.7, max_tokens=500 |
| 下一题生成 | gpt-4o | temperature=0.7, max_tokens=500 |
| 报告生成 | gpt-4o | temperature=0.3, max_tokens=4000, response_format=json_object |
| 语音转写 | whisper-1 | language=zh |
| 语音合成 | tts-1 | voice=alloy, response_format=mp3 |

环境变量：

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_WHISPER_MODEL=whisper-1
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=alloy
OPENAI_TIMEOUT_SECONDS=60
OPENAI_MAX_RETRIES=2
```

### 5.2 重试策略

```python
# 伪代码 — 实现时必须遵循
for attempt in range(OPENAI_MAX_RETRIES + 1):
    try:
        response = await openai_client.call(...)
        return response
    except (Timeout, RateLimit, APIError) as e:
        if attempt == OPENAI_MAX_RETRIES:
            raise AppException(code=50201, message="AI 服务暂时不可用")
        await asyncio.sleep(1)
```

### 5.3 Prompt 文件路径与变量

| 文件 | 用途 | 模板变量 |
|------|------|---------|
| `interview_system_prompt.txt` | System message（所有面试 LLM 调用） | `{job_role_name}`, `{difficulty_label}`, `{max_questions}` |
| `interview_first_question_prompt.txt` | 生成第一题 User message | 无 |
| `interview_next_question_prompt.txt` | 生成下一题 User message | `{conversation_history}`, `{question_count}`, `{max_questions}` |
| `interview_report_prompt.txt` | 生成报告 User message | `{job_role_name}`, `{difficulty_label}`, `{conversation_history}`, `{question_count}` |

**难度标签映射（代码中写死）：**

| difficulty | difficulty_label |
|------------|-----------------|
| junior | 初级（应届生/1年以内） |
| mid | 中级（1-3年经验） |
| senior | 高级（3年以上经验） |

---

## 6. Prompt 模板全文（verbatim，禁止修改语义）

### 6.1 `backend/app/prompts/interview_system_prompt.txt`

```
你是一位专业的{job_role_name}面试官，正在进行一场{difficulty_label}水平的模拟面试。

规则：
1. 使用简体中文提问。
2. 每次只提出一个问题，不要一次提出多个问题。
3. 问题应与{job_role_name}岗位相关，难度匹配{difficulty_label}水平。
4. 问题类型应多样化，包括：自我介绍、项目经验、技术深度、问题解决、场景设计、行为面试等。
5. 不要回答候选人的问题，不要提供提示或答案。
6. 不要重复已经问过的问题。
7. 本次面试最多{max_questions}个问题。
8. 保持专业、友好的面试官语气。
9. 输出 ONLY 问题文本，不要加任何前缀（如"问题："）或后缀说明。
```

### 6.2 `backend/app/prompts/interview_first_question_prompt.txt`

```
请给出本次模拟面试的第一个问题。如果是自我介绍类问题，请明确邀请候选人自我介绍。
```

### 6.3 `backend/app/prompts/interview_next_question_prompt.txt`

```
以下是截至目前面试的对话记录：

{conversation_history}

当前已提问 {question_count} 个问题，最多 {max_questions} 个问题。

请根据候选人的回答，给出下一个面试问题。
- 如果候选人的回答过于简短或偏离主题，可以追问或换一个相关话题。
- 如果已达到 {max_questions} 个问题，请输出 exactly: [INTERVIEW_COMPLETE]
- 否则，输出下一个问题文本。
```

### 6.4 `backend/app/prompts/interview_report_prompt.txt`

```
你是一位资深的{job_role_name}面试评估专家。请根据以下{difficulty_label}水平的模拟面试对话记录，生成一份结构化的面试评估报告。

对话记录：
{conversation_history}

共进行了 {question_count} 轮问答。

请严格按照以下 JSON 格式输出，不要输出任何其他内容：

{
  "overallScore": <0-100的数值，保留2位小数>,
  "communicationScore": <0-100，表达清晰度、逻辑性>,
  "technicalScore": <0-100，技术知识深度与准确性>,
  "problemSolvingScore": <0-100，分析与解决问题能力>,
  "structureScore": <0-100，回答结构完整性（如STAR法则）>,
  "strengths": ["优点1", "优点2", ...],
  "weaknesses": ["不足1", "不足2", ...],
  "suggestions": ["建议1", "建议2", "建议3"],
  "questionFeedback": [
    {
      "sequence": <interviewer消息的sequence，整数>,
      "question": "<问题原文>",
      "answerSummary": "<候选人回答的简要概括，50字以内>",
      "score": <0-100，该题得分>,
      "feedback": "<该题的具体改进建议，100字以内>"
    }
  ],
  "summary": "<200-500字的总体评价和改进方向>"
}

评分标准：
- 60分以下：不合格，存在明显短板
- 60-74分：基本合格，有提升空间
- 75-89分：良好，表现不错
- 90-100分：优秀，表现出色

strengths 数组 2-5 条，weaknesses 数组 2-5 条，suggestions 数组 3-5 条。
questionFeedback 数组长度必须等于 {question_count}，每条对应一个 interviewer 问题。
```

### 6.5 conversation_history 格式

Service 层组装，格式如下（每条一行）：

```
面试官：{interviewer content}
候选人：{candidate content}
面试官：{interviewer content}
候选人：{candidate content}
...
```

---

## 7. OpenAI Service 接口设计

### 7.1 `OpenAIService` 方法

```python
class OpenAIService:
    async def generate_first_question(
        self,
        job_role_name: str,
        difficulty: str,
        max_questions: int,
    ) -> str:
        """返回第一个问题文本"""

    async def generate_next_question(
        self,
        job_role_name: str,
        difficulty: str,
        max_questions: int,
        question_count: int,
        messages: list[InterviewMessage],
    ) -> tuple[str, bool]:
        """返回 (question_text, is_finished)。
        若 LLM 输出 [INTERVIEW_COMPLETE] 或 question_count >= max_questions，is_finished=True"""

    async def generate_report(
        self,
        job_role_name: str,
        difficulty: str,
        question_count: int,
        messages: list[InterviewMessage],
    ) -> dict:
        """返回解析后的 report JSON dict，字段名 camelCase"""

    async def transcribe_audio(
        self,
        file_path: str,
    ) -> str:
        """返回转写文本"""

    async def synthesize_speech(
        self,
        text: str,
    ) -> bytes:
        """返回 mp3 bytes"""
```

### 7.2 LLM 响应处理

| 场景 | 处理 |
|------|------|
| 首题/下一题 | 去除首尾空白；若含 `[INTERVIEW_COMPLETE]` → is_finished=True |
| 报告 | json.loads；校验必填字段；校验分数范围 0-100；失败则 report_status=failed |
| 转写 | 去除首尾空白；空文本抛 50201 |
| TTS | 保存至 `uploads/tts/{session_id}/{message_id}.mp3` |

---

## 8. 安全架构

### 8.1 认证

- 算法：JWT HS256
- Access Token 有效期：900 秒（15 分钟）
- Refresh Token 有效期：604800 秒（7 天）
- Refresh Token 存储：SHA-256 哈希后存 DB
- Rotation：每次 refresh 吊销旧 token，签发新对

### 8.2 授权

- 所有 `/api/v1/*` 端点（除 auth 和 health）需 Bearer Token
- 资源访问校验：`session.user_id == current_user.id`，否则 403

### 8.3 数据安全

- 密码：bcrypt cost=12
- 音频文件：存储在 `uploads/audio/{session_id}/`，仅通过认证 API 访问
- 日志：禁止记录 password、token 明文、OpenAI API Key

---

## 9. 部署架构

### 9.1 开发环境 docker-compose

```yaml
# docker-compose.yml 规格
services:
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: mockinterview
      POSTGRES_PASSWORD: mockinterview
      POSTGRES_DB: mockinterview
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    depends_on: [postgres, redis]
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
```

### 9.2 环境变量清单

| 变量 | 示例 | 必填 |
|------|------|------|
| DATABASE_URL | postgresql+asyncpg://mockinterview:mockinterview@postgres:5432/mockinterview | 是 |
| REDIS_URL | redis://redis:6379/0 | 是 |
| JWT_SECRET | your-256-bit-secret | 是 |
| JWT_ALGORITHM | HS256 | 是 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 15 | 是 |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | 是 |
| OPENAI_API_KEY | sk-... | 是 |
| OPENAI_MODEL | gpt-4o | 是 |
| CORS_ORIGINS | * | 否（开发） |
| UPLOAD_DIR | /app/uploads | 是 |
| LOG_LEVEL | INFO | 否 |

### 9.3 Flutter 配置

```
# mobile/.env
API_BASE_URL=http://10.0.2.2:8000/api/v1   # Android 模拟器
# API_BASE_URL=http://localhost:8000/api/v1  # iOS 模拟器
```

---

## 10. 后台任务：报告生成

```python
# 伪代码 — complete 接口中触发
async def _generate_report_task(session_id: UUID):
    try:
        # 1. report_status = generating（已在 complete 中设置）
        # 2. 加载 session + messages + job_role
        # 3. 调用 openai_service.generate_report()
        # 4. 解析 JSON，写入 interview_reports
        # 5. report_status = ready
    except Exception:
        # report_status = failed
        # 记录 error 日志
        pass
```

- 使用 `asyncio.create_task()` 触发，不阻塞 complete 响应
- **重要：** 后台任务必须创建独立的 `AsyncSession`（通过 `async_session_factory()`），禁止复用 HTTP 请求级 session（请求返回后 session 自动关闭，复用将导致 `SessionClosed` 错误）
- 同一 session 不可重复生成（report 表 session_id UNIQUE）

---

## 11. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-12 | 初始版本 |
