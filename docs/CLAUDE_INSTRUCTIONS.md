# MockInterview AI — Claude Code 执行手册

> 版本：1.0.0  
> 最后更新：2026-06-12  
> 本文档是 Claude Code 自动开发的首要入口

---

## 1. 角色定位

你是 **执行型工程师**，不是产品设计师。

| 你应该做 | 你不应该做 |
|---------|-----------|
| 按 TASKS.md 顺序实现代码 | 自行设计业务逻辑 |
| 严格遵循 API/DATABASE/PRD 规格 | 增删 API 字段或端点 |
| 复制 ARCHITECTURE 中的 Prompt 原文 | 改写 Prompt 语义 |
| 遇到文档未覆盖的问题时停止并提问 | 猜测或自行决定 |
| 每项任务完成后自检验收标准 | 跳过任务或合并多个任务 |

---

## 2. 必读文档与顺序

按以下顺序阅读，后读文档以前读文档为准：

```
1. CLAUDE_INSTRUCTIONS.md  ← 你正在读的文件
2. TASKS.md                  ← 找到当前要执行的任务 ID
3. API.md                    ← 当前任务涉及的端点
4. DATABASE.md               ← 当前任务涉及的表/字段
5. PRD.md                    ← 当前任务涉及的业务规则
6. ARCHITECTURE.md           ← 当前任务涉及的架构/Prompt/时序
7. CODING_STANDARD.md        ← 编码时随时参照
```

---

## 3. 执行流程

### 3.1 每个任务的标准流程

```
1. 阅读 TASKS.md 中当前任务 ID 的完整描述
2. 阅读「参考」列指向的文档章节
3. 仅修改「产出」列列出的文件（及必要的 import/注册）
4. 运行 lint / test
5. 逐条核对「验收标准」
6. Commit（格式见 CODING_STANDARD.md §1.1）
7. 更新任务状态
8. 进入下一个任务 ID
```

**注意：** 每个 TASK 完成后仅 Commit，禁止 Push 或创建 PR。

### 3.2 Sprint 完成流程

Sprint 划分见 [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) §4。当一个 Sprint 内的全部 TASK 均已完成时：

```
1. 确认本 Sprint 所有 TASK 均已 Commit
2. 执行验证（lint / typecheck / test）
3. git push origin 当前分支
4. 创建 Pull Request
5. 更新 Sprint 状态
```

**开始 Sprint 时：**

- 创建分支 `feature/sprint-{n}-{slug}`（如 `feature/sprint-1-infrastructure`）
- 同一 Sprint 内所有 TASK 在同一分支上连续 Commit

**PR 必须包含：**

- 功能说明
- 修改文件
- 测试结果
- 风险分析
- 对应 Sprint
- 包含任务

完整 Git 规则见 [CLAUDE.md](../CLAUDE.md)。

### 3.3 任务状态追踪

- 当前任务 ID 应在 commit message 中体现
- 不要并行执行多个任务
- 不要回退修改已完成任务的验收标准

### 3.4 遇到以下情况必须停止并提问

- 文档中存在矛盾（如 API 与 DATABASE 字段不一致）
- 当前任务需要修改文档未列出的文件且无法避免
- 第三方库 API 与文档假设不兼容
- OpenAI API 行为与 Prompt 预期不符
- 验收标准无法在当前环境验证

---

## 4. 项目结构速查

```
MockInterview_AI/
├── backend/          # FastAPI 后端
├── mobile/           # Flutter 移动端
├── docs/             # 全部规格文档（只读，不得修改除非用户要求）
├── docker-compose.yml
└── README.md
```

---

## 5. 环境变量清单

### 5.1 后端 (`backend/.env`)

| 变量 | 必填 | 示例值 | 说明 |
|------|------|--------|------|
| DATABASE_URL | 是 | postgresql+asyncpg://mockinterview:mockinterview@localhost:5432/mockinterview | 数据库连接 |
| REDIS_URL | 是 | redis://localhost:6379/0 | Redis 连接 |
| JWT_SECRET | 是 | change-me-to-random-256-bit-string | JWT 签名密钥 |
| JWT_ALGORITHM | 是 | HS256 | JWT 算法 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 是 | 15 | Access Token 有效期 |
| REFRESH_TOKEN_EXPIRE_DAYS | 是 | 7 | Refresh Token 有效期 |
| OPENAI_API_KEY | 是 | sk-... | OpenAI API 密钥 |
| OPENAI_MODEL | 是 | gpt-4o | 对话/报告模型 |
| OPENAI_WHISPER_MODEL | 是 | whisper-1 | 转写模型 |
| OPENAI_TTS_MODEL | 是 | tts-1 | TTS 模型 |
| OPENAI_TTS_VOICE | 是 | alloy | TTS 语音 |
| OPENAI_TIMEOUT_SECONDS | 是 | 60 | OpenAI 超时 |
| OPENAI_MAX_RETRIES | 是 | 2 | 重试次数 |
| UPLOAD_DIR | 是 | /app/uploads | 上传目录 |
| CORS_ORIGINS | 否 | * | CORS 允许源 |
| LOG_LEVEL | 否 | INFO | 日志级别 |

### 5.2 移动端 (`mobile/.env`)

| 变量 | 必填 | 示例值 | 说明 |
|------|------|--------|------|
| API_BASE_URL | 是 | http://10.0.2.2:8000/api/v1 | 后端 API 地址（Android 模拟器） |

---

## 6. 启动命令

### 6.1 首次启动

```bash
# 1. 启动基础设施
docker-compose up -d postgres redis

# 2. 后端
cd backend
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY 和 JWT_SECRET
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 移动端
cd mobile
cp .env.example .env
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter run
```

### 6.2 运行测试

```bash
# 后端
cd backend
pytest -v

# 移动端
cd mobile
flutter analyze
flutter test
```

---

## 7. Prompt 文件规则

### 7.1 文件位置

| 文件 | 路径 |
|------|------|
| System Prompt | `backend/app/prompts/interview_system_prompt.txt` |
| 首题 Prompt | `backend/app/prompts/interview_first_question_prompt.txt` |
| 下一题 Prompt | `backend/app/prompts/interview_next_question_prompt.txt` |
| 报告 Prompt | `backend/app/prompts/interview_report_prompt.txt` |

### 7.2 规则

- 内容必须与 ARCHITECTURE.md §6 **完全一致**（verbatim copy）
- 仅允许在代码中替换 `{变量名}` 占位符
- 不得翻译、缩写、增删规则条目
- 不得调整 JSON 输出格式要求

### 7.3 变量替换

| 变量 | 来源 |
|------|------|
| `{job_role_name}` | job_roles.name_zh |
| `{difficulty_label}` | junior→初级（应届生/1年以内）, mid→中级（1-3年经验）, senior→高级（3年以上经验） |
| `{max_questions}` | session.max_questions（默认 8） |
| `{question_count}` | session.question_count |
| `{conversation_history}` | 按 ARCHITECTURE §6.5 格式组装 |

---

## 8. 关键业务逻辑速查（禁止自行修改）

### 8.1 面试状态机

```
pending → in_progress → completed
                     ↘ cancelled
                     ↘ failed
```

### 8.2 报告状态机

```
pending → generating → ready
                    ↘ failed
```

### 8.3 核心数字

| 常量 | 值 |
|------|-----|
| max_questions | 8 |
| access_token_expire | 900 秒 |
| refresh_token_expire | 7 天 |
| 报告轮询间隔 | 2 秒 |
| 报告轮询最大次数 | 60 |
| 音频最大大小 | 25 MB |
| 回答最大长度 | 5000 字符 |
| bcrypt cost | 12 |

### 8.4 预置岗位 code

`frontend`, `backend`, `fullstack`, `mobile`, `product`, `data_analyst`, `algorithm`, `test_engineer`

### 8.5 难度枚举

`junior`, `mid`, `senior`

### 8.6 模式枚举

`text`, `voice`

---

## 9. API 端点速查

| Method | Path | 认证 |
|--------|------|------|
| POST | /auth/register | 否 |
| POST | /auth/login | 否 |
| POST | /auth/refresh | 否 |
| POST | /auth/logout | 是 |
| GET | /users/me | 是 |
| PATCH | /users/me | 是 |
| GET | /job-roles | 是 |
| POST | /interviews | 是 |
| GET | /interviews | 是 |
| GET | /interviews/{id} | 是 |
| POST | /interviews/{id}/start | 是 |
| POST | /interviews/{id}/messages | 是 |
| POST | /interviews/{id}/complete | 是 |
| POST | /interviews/{id}/cancel | 是 |
| POST | /interviews/{id}/transcribe | 是 |
| GET | /interviews/{id}/report | 是 |
| GET | /interviews/{id}/report/status | 是 |
| GET | /interviews/{id}/messages/{messageId}/tts | 是 |
| GET | /health | 否 |

完整 Schema 见 [API.md](./API.md)。

---

## 10. 数据库表速查

| 表名 | 用途 |
|------|------|
| users | 用户 |
| refresh_tokens | 刷新令牌 |
| job_roles | 预置岗位（8 条 seed） |
| interview_sessions | 面试会话 |
| interview_messages | 面试消息 |
| interview_reports | 评分报告 |

完整 DDL 见 [DATABASE.md](./DATABASE.md)。

---

## 11. 任务执行顺序

从 **T001** 开始，到 **T040** 结束。共 40 项。

```
T001 → T002 → T003 → T004 → T005 →
T006 → T007 → T008 → T009 →
T010 → T011 → T012 → T013 →
T014 → T015 → T016 →
T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 →
T027 → T028 → T029 →
T030 → T031 → T032 → T033 → T034 →
T035 → T036 → T037 → T038 →
T039 → T040
```

详细描述见 [TASKS.md](./TASKS.md)。

---

## 12. 完成定义（Definition of Done）

全部 40 项任务满足以下条件时，项目 MVP 完成：

### 12.1 自动化检查

- [ ] `docker-compose up` 可启动 postgres + redis + backend
- [ ] `alembic upgrade head` 成功，8 条 job_roles seed 存在
- [ ] `pytest -v` 全部通过
- [ ] `flutter analyze` 零 error
- [ ] `GET /health` 返回 200

### 12.2 端到端流程

按 [E2E_CHECKLIST.md](./E2E_CHECKLIST.md)（T040 产出）手工验证：

- [ ] 注册 → 登录
- [ ] 选择岗位/难度/模式 → 创建面试
- [ ] 文字模式完成 3+ 轮 Q&A
- [ ] 结束面试 → 报告生成 → 查看报告
- [ ] 历史记录可见
- [ ] 退出登录

### 12.3 代码质量

- [ ] 无 hardcoded secrets
- [ ] 符合 CODING_STANDARD.md
- [ ] Prompt 文件与 ARCHITECTURE §6 verbatim 一致

---

## 13. 文档修改规则

| 文档 | Claude Code 是否可修改 |
|------|----------------------|
| PRD.md | **否** |
| ARCHITECTURE.md | **否** |
| DATABASE.md | **否** |
| API.md | **否** |
| TASKS.md | **否** |
| CODING_STANDARD.md | **否** |
| CLAUDE_INSTRUCTIONS.md | **否** |
| README.md | 是（T039 任务） |
| E2E_CHECKLIST.md | 是（T040 任务） |
| 源代码 | 是（按 TASKS 产出列） |

若发现文档错误，停止执行并报告用户，不得自行修改规格文档。

---

## 14. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-12 | 初始版本 |
| 1.0.1 | 2026-06-12 | Git 工作流改为 Sprint 级 Push/PR |
