# MockInterview AI — 开发计划

> 版本：1.0.1  
> 最后更新：2026-06-14  
> 基于：TASKS.md v1.0.3（40 项任务）  
> 关联文档：[TASKS.md](./TASKS.md) | [ARCHITECTURE.md](./ARCHITECTURE.md) | [CLAUDE_INSTRUCTIONS.md](./CLAUDE_INSTRUCTIONS.md)

---

## 1. 总览

| 指标 | 数值 |
|------|------|
| 总任务数 | 40 |
| 预估总工时 | 120–160 小时（每项 ≤ 4h） |
| 关键路径长度 | 19 项任务（~57–76h） |
| Sprint 数 | 7 |
| 预估周期 | 14–20 个工作日 |

---

## 2. 关键路径分析

### 2.1 关键路径（最长依赖链）

决定项目最短完成时间的路径：

```
T001 → T002 → T003 → T006 → T007 → T009 → T017 → T018 → T019 → T021 → T028 → T029 → T037 → T039 → T040
 P0      P0      P0      P1      P1      P1      P4      P4      P4      P4      P5      P5      P7      P8      P8
```

共 **15 项任务串行**，加上 T029 等待 T024（19 项），为项目绝对下限。

### 2.2 次关键路径（报告线）

```
...T009 → T017 → T018 → T019 → T031 → T032 → T033 → T037...
```

18 项任务。报告系统是第二大瓶颈。

### 2.3 移动端路径（有充裕缓冲）

```
T001 → T004 → T005 → T013 → T016 → T024 → T029 → T037
```

8 项任务。移动端等待后端的时间远多于自身开发时间，**有约 11 项任务的缓冲**。

---

## 3. 任务依赖全景图

```
                    ┌─────────────────────────────────────────────────────────────────────┐
                    │                        DEPENDENCY GRAPH                             │
                    └─────────────────────────────────────────────────────────────────────┘

                    ┌───────┐     ┌───────┐     ┌───────┐
                    │ T001  │────▶│ T002  │────▶│ T003  │
                    │docker │     │fastapi│     │alembic│
                    └───┬───┘     └───┬───┘     └───┬───┘
                        │             │              │
                        │             │         ┌────▼────┐     ┌───────┐
                        │             │         │  T006   │────▶│ T007  │
                        │             │         │mig 1-3  │     │mig 4-6│
                        │             │         └────┬────┘     └───┬───┘
                        │             │              │              │
                        │             │         ┌────▼────┐    ┌────▼────┐
                        │             │         │  T008   │    │  T009   │
                        │             │         │  seed   │    │model+sch│
                        │             │         └─────────┘    └────┬────┘
                        │             │                    ┌────────┼────────┐
                        │             │                    │        │        │
                   ┌────▼────┐   ┌────▼────┐         ┌────▼──┐ ┌──▼───┐ ┌──▼───┐
                   │  T004   │   │  T005   │         │ T010  │ │T017  │ │T025  │
                   │ flutter │◀──│ shared  │         │ jwt   │ │openai│ │fz mod│
                   └────┬────┘   └─────────┘         └───┬───┘ └──┬───┘ └──┬───┘
                        │                                │        │        │
                   ┌────▼────┐                      ┌────▼───┐  ┌─▼────┐   │
                   │  T013   │                      │  T011  │  │T018  │   │
                   │ fl auth │                      │auth svc│  │1st/nx│   │
                   └────┬────┘                      └────┬───┘  └──┬───┘   │
                        │                                │         │       │
                   ┌────▼────┐                     ┌─────▼───┐  ┌──▼────┐  │
                   │  T016   │                     │  T012   │  │ T019  │  │
                   │home/setup│◀───────────────────│auth rts │  │state  │  │
                   └────┬────┘                     └────┬───┘  └──┬────┘  │
                        │                               │         │       │
                        │                          ┌────▼──┐ ┌────▼──┐    │
                        │                          │ T014  │ │T020-23│    │
                        │                          │jobrole│ │int API│    │
                        │                          └───┬───┘ └───┬───┘    │
                        │                              │         │        │
                        │                          ┌───▼──┐      │        │
                        │                          │T015  │      │        │
                        │                          │users │      │        │
                        │                          └───┬──┘      │        │
                        │                              │         │        │
                   ┌────▼──────────────────────────────▼─────────▼───┐    │
                   │                     T024                         │◀───┘
                   │              Flutter Session Page                │
                   └──────────────────────┬───────────────────────────┘
                                          │
                ┌─────────────────────────┼───────────────────────┐
                │                         │                       │
           ┌────▼────┐              ┌─────▼─────┐          ┌──────▼─────┐
           │  T029   │              │   T033    │          │   T035     │
           │fl voice │              │ fl report │          │ fl history │
           └────┬────┘              └─────┬─────┘          └──────┬─────┘
                │                         │                       │
                │         ┌───────────────┼───────────────────────┘
                │         │               │
           ┌────▼─────────▼───────────────▼─────┐
           │              T037                   │
           │       Flutter Integration           │
           └──────────────┬──────────────────────┘
                          │
                     ┌────▼────┐     ┌───────┐
                     │  T039   │────▶│ T040  │
                     │  README │     │  E2E  │
                     └─────────┘     └───────┘
```

---

## 4. Sprint 划分

### Sprint 1 — 基础设施搭建（P0）

> **目标：** 双端脚手架就绪，docker-compose 可启动，健康检查通过  
> **任务数：** 5 | **预估工时：** 15–20h  
> **里程碑：** `GET /health` 返回 200 + Flutter 空白 App 可编译

| 任务 | 标题 | 依赖 | 预估 | 风险 | 影响文件 |
|------|------|------|------|------|---------|
| T001 | Monorepo + docker-compose | — | 2–3h | 🟢 低 | `docker-compose.yml`, `README.md`, `.gitignore` |
| T002 | FastAPI 脚手架 | T001 | 3–4h | 🟡 中 | `backend/requirements.txt`, `backend/Dockerfile`, `backend/app/main.py`, `backend/app/core/config.py`, `backend/.env.example` |
| T003 | Alembic 初始化 | T002 | 2–3h | 🟡 中 | `backend/alembic/`, `backend/app/db/base.py`, `backend/app/db/session.py` |
| T004 | Flutter 脚手架 | T001 | 3–4h | 🟡 中 | `mobile/` 完整目录 |
| T005 | 共享常量与异常类 | T002, T004 | 3–4h | 🟢 低 | `backend/app/core/exceptions.py`, `backend/app/core/logging.py`, `mobile/lib/core/constants/api_constants.dart`, `mobile/lib/core/network/api_exception.dart` |

**⚡ 并行机会：** T004（Flutter）与 T002+T003（Backend）可完全并行  
**⚠️ Sprint 风险点：**

| 风险 | 说明 | 缓解 |
|------|------|------|
| T002 依赖版本冲突 | SQLAlchemy 2.x async + asyncpg + pydantic v2 兼容性 | 使用 `sqlalchemy[asyncio]>=2.0`, `pydantic>=2.0`, 验证 `pip install` 无冲突 |
| T003 async session factory | asyncpg 连接池配置不当导致启动超时 | 确认 `DATABASE_URL` 使用 `postgresql+asyncpg://` 协议 |
| T004 Flutter SDK 版本 | `flutter create` 需要 Flutter 3.x stable | 确认环境 `flutter --version` ≥ 3.0 |

---

### Sprint 2 — 数据层（P1）

> **目标：** 6 张表 + 8 条种子数据 + ORM + Pydantic Schema 全部就绪  
> **任务数：** 4 | **预估工时：** 12–16h  
> **里程碑：** `alembic upgrade head` 成功，`job_roles` 有 8 条数据

| 任务 | 标题 | 依赖 | 预估 | 风险 | 影响文件 |
|------|------|------|------|------|---------|
| T006 | Migration 001-003 | T003 | 3–4h | 🟡 中 | `alembic/versions/001_create_job_roles.py`, `002_create_users.py`, `003_create_refresh_tokens.py` |
| T007 | Migration 004-006 | T006 | 3–4h | 🟢 低 | `alembic/versions/004_create_interview_sessions.py`, `005_create_interview_messages.py`, `006_create_interview_reports.py` |
| T008 | 种子数据 007 | T006 | 1–2h | 🟢 低 | `alembic/versions/007_seed_job_roles.py` |
| T009 | Models + Schemas | T007 | 4h | 🟡 中 | `backend/app/models/*.py` (6 files), `backend/app/schemas/*.py` (5 files) |

**⚡ 并行机会：** T008 与 T007 可并行（均仅依赖 T006）  
**🔒 文件冲突热点：**

| 文件 | 涉及任务 | 冲突类型 |
|------|---------|---------|
| `alembic/versions/` | T006, T007, T008 | 各任务独立文件，无冲突 |
| `backend/app/models/` | T009 创建，后续 T019/T031 读取 | 只读引用，无冲突 |

**⚠️ Sprint 风险点：**

| 风险 | 说明 | 缓解 |
|------|------|------|
| T006 部分唯一索引 | `uq_users_email_active UNIQUE (email) WHERE deleted_at IS NULL` 是 PostgreSQL 特有语法，Alembic autogenerate 可能不识别 | 手写 migration，不依赖 autogenerate；`alembic upgrade head` 后验证 `\d users` |
| T009 camelCase alias 遗漏 | Pydantic v2 `alias_generator=to_camel` 需每个 Schema 正确配置 | T009 验收时逐 Schema 对比 API.md §2 |
| T009 JSONB 字段映射 | `strengths/weaknesses/suggestions/question_feedback` 是 JSONB，SQLAlchemy 需 `JSON` 类型 + Pydantic `list` | 确认 Model 使用 `Column(JSON)` 而非 `Column(Text)` |

---

### Sprint 3 — 认证系统（P2 + P4 前段）

> **目标：** 完整认证链路（注册/登录/刷新/退出）+ OpenAI Service 基础  
> **任务数：** 7 | **预估工时：** 21–28h  
> **里程碑：** 4 个 Auth API 可用 + Flutter 登录/注册页面可交互 + Prompt 文件就绪

| 任务 | 标题 | 依赖 | 预估 | 风险 | 影响文件 |
|------|------|------|------|------|---------|
| T010 | JWT + bcrypt 工具 | T009 | 2–3h | 🟢 低 | `backend/app/core/security.py` |
| T011 | AuthService | T010 | 4h | 🟡 中 | `backend/app/services/auth_service.py` |
| T012 | Auth Routes | T011 | 3–4h | 🟡 中 | `backend/app/api/v1/auth.py`, `backend/app/api/deps.py`, `backend/app/api/v1/router.py` |
| T017 | OpenAI Service 基础 | T009 | 3–4h | 🟡 中 | `backend/app/services/openai_service.py`, `backend/app/prompts/*.txt` (4 files) |
| T018 | 首题/下一题生成 | T017 | 3–4h | 🔴 高 | `backend/app/services/openai_service.py` |
| T013 | Flutter 认证模块 | T004, T005 | 4h | 🟡 中 | `mobile/lib/features/auth/**`, `mobile/lib/core/network/dio_client.dart`, `mobile/lib/core/network/auth_interceptor.dart`, `mobile/lib/core/storage/secure_storage.dart` |
| T025 | Flutter Interview Models | T013, T009 | 3–4h | 🟢 低 | `mobile/lib/features/interview/data/**`, `mobile/lib/shared/models/**` |

**⚡ 并行机会：** T010→T011→T012（Backend Auth）与 T017→T018（OpenAI）与 T013→T025（Flutter）三条线可完全并行  
**🔒 文件冲突热点：**

| 文件 | 涉及任务 | 冲突类型 |
|------|---------|---------|
| `backend/app/api/v1/router.py` | T012 首次注册路由，后续 T014/T015/T020 追加 | 每次追加一行 `router.include_router()`，低风险 |

**⚠️ Sprint 风险点：**

| 风险 | 说明 | 缓解 |
|------|------|------|
| T010 refresh token 长度 | 必须生成 128 hex chars（64 bytes），与 API.md 一致 | 使用 `secrets.token_hex(64)` = 128 chars ✅ |
| T012 `get_current_user` 依赖 | 必须同时校验 `deleted_at IS NULL`，否则已软删除用户可登录 | `deps.py` 查询加 `WHERE deleted_at IS NULL` |
| T017 Prompt 文件完整性 | 必须与 ARCHITECTURE §6 verbatim 一致，禁止任何语义修改 | 逐字符对比，使用 diff 验证 |
| T018 `[INTERVIEW_COMPLETE]` 检测 | LLM 可能不严格输出方括号标记 | 代码中同时检查 `question_count >= max_questions` 作为兜底 |
| T013 AuthInterceptor 死循环 | refresh 请求本身返回 401 时，可能触发无限递归 | 对 `/auth/refresh` 路径豁免 interceptor；refresh 失败时清除 token 并跳转登录页 |

---

### Sprint 4 — API 层与 Flutter 页面（P3 + P4 前段）

> **目标：** 全部后端面试 API + Flutter 首页/设置页  
> **任务数：** 8 | **预估工时：** 24–32h  
> **里程碑：** 创建面试→start→messages→complete/cancel 全链路 API 可调通

| 任务 | 标题 | 依赖 | 预估 | 风险 | 影响文件 |
|------|------|------|------|------|---------|
| T014 | Job Roles API | T012 | 2–3h | 🟢 低 | `backend/app/api/v1/job_roles.py` |
| T015 | Users API | T012 | 2–3h | 🟢 低 | `backend/app/services/user_service.py`, `backend/app/api/v1/users.py` |
| T016 | Flutter 首页与设置页 | T013, T014 | 4h | 🟡 中 | `mobile/lib/features/home/**`, `mobile/lib/features/interview/presentation/setup/**`, `mobile/lib/app/router.dart` |
| T019 | InterviewService 状态机 | T018 | 4h | 🔴 高 | `backend/app/services/interview_service.py` |
| T020 | Interview API: CRUD | T019 | 3–4h | 🟡 中 | `backend/app/api/v1/interviews.py` (创建/列表/详情) |
| T021 | Interview API: start | T019 | 2–3h | 🟡 中 | `backend/app/api/v1/interviews.py` (追加) |
| T022 | Interview API: messages | T019 | 3–4h | 🔴 高 | `backend/app/api/v1/interviews.py` (追加) |
| T023 | Interview API: complete/cancel | T019 | 2–3h | 🟡 中 | `backend/app/api/v1/interviews.py` (追加) |

**⚡ 并行机会：** T014+T015（简单 API）与 T019→T020-23（核心面试）与 T016（Flutter）可并行  
**🔒 文件冲突热点（本 Sprint 最密集）：**

| 文件 | 涉及任务 | 冲突类型 |
|------|---------|---------|
| **`backend/app/api/v1/interviews.py`** | **T020, T021, T022, T023, T027, T028, T032** | **⚠️ 高风险 — 7 个任务顺序追加端点** |
| `backend/app/api/v1/router.py` | T014, T015, T020 | 追加 `include_router()` |

> **关键约束：** `interviews.py` 被 7 个任务修改，必须严格按 T020→T021→T022→T023→T027→T028→T032 顺序追加，禁止并行。

**⚠️ Sprint 风险点：**

| 风险 | 说明 | 缓解 |
|------|------|------|
| T019 状态机边界条件 | `pending` 下 cancel 允许但 question_count=0；`in_progress` 下 cancel 仅 question_count=0 | 编写 6 个状态转换测试用例覆盖全部路径 |
| T019 sequence 奇偶规则 | interviewer=奇数(1,3,5), candidate=偶数(2,4,6)；`next_sequence = max(seq) + 1` | 在 service 层 assert 校验；DB UNIQUE 约束兜底 |
| T022 question_count 与 max_questions 同步 | AI 生成新问题时 question_count++ 必须与 INSERT message 在同一事务 | 使用 DB 事务包裹：INSERT message + UPDATE question_count |
| T022 OpenAI 调用中 session 状态变化 | 用户快速连续提交，前一个 OpenAI 调用未完成时收到第二个请求 | 对 submit_answer 加 session 级悲观锁（`SELECT ... FOR UPDATE`） |
| T016 路由配置 | GoRouter 认证 redirect 逻辑复杂，无 token 时需拦截所有认证路由 | 使用 `redirect` 回调统一处理，不逐路由判断 |

---

### Sprint 5 — 面试集成与测试（P4 后段）

> **目标：** Flutter 面试会话页完整跑通 + 后端单元测试 + 语音/报告后端  
> **任务数：** 7 | **预估工时：** 21–28h  
> **里程碑：** 文字模式端到端流程（Flutter↔Backend）可演示

| 任务 | 标题 | 依赖 | 预估 | 风险 | 影响文件 |
|------|------|------|------|------|---------|
| T024 | Flutter 面试会话页 | T016, T021, T022, T023 | 4h | 🔴 高 | `mobile/lib/features/interview/presentation/session/**` |
| T030 | OpenAI 报告生成 | T017 | 3–4h | 🔴 高 | `backend/app/services/openai_service.py` (追加) |
| T031 | ReportService 异步生成 | T030, T019 | 4h | 🔴 高 | `backend/app/services/report_service.py` |
| T026 | Interview 单元测试 | T023 | 3–4h | 🟡 中 | `backend/tests/test_interview_service.py`, `backend/tests/conftest.py` |
| T027 | Whisper 转写 API | T017, T020 | 3–4h | 🟡 中 | `openai_service.py` (追加), `interviews.py` (追加) |
| T028 | TTS 音频 API | T017, T021 | 3–4h | 🟡 中 | `openai_service.py` (追加), `interviews.py` (追加) |
| T034 | Report 单元测试 | T031 | 2–3h | 🟢 低 | `backend/tests/test_report_service.py` |

**⚡ 并行机会：** T024（Flutter UI）与 T030→T031（报告后端）与 T026（测试）可并行；T027/T028 互相独立  
**🔒 文件冲突热点：**

| 文件 | 涉及任务 | 冲突类型 |
|------|---------|---------|
| `backend/app/services/openai_service.py` | T030, T027, T028 | 追加方法，无覆盖风险 |
| `backend/app/api/v1/interviews.py` | T027, T028 | 追加端点 |
| `backend/tests/conftest.py` | T026 创建，T034/T038 追加 | 追加 fixture |

**⚠️ Sprint 风险点（本 Sprint 风险最密集）：**

| 风险 | 说明 | 缓解 |
|------|------|------|
| **T024 Flutter↔Backend 集成** | 首次端到端联调，camelCase 映射、响应结构、错误码全部需要验证 | 先跑通 1 轮 Q&A，再扩展到 8 轮完整流程 |
| **T030 LLM JSON 输出不可靠** | GPT-4o 可能输出 markdown 代码块包裹的 JSON、多余文本、字段缺失 | `response_format=json_object` + 代码侧 `json.loads` + 必填字段校验 + 失败时 `report_status=failed` |
| **T031 asyncio task session 管理** | 后台任务复用请求级 session 导致 `SessionClosed` | 在 `_generate_report_task` 入口处创建独立 `AsyncSession`（ARCHITECTURE §10 已标注） |
| **T031 report 生成中间崩溃** | 服务器重启时 task 丢失，session 永远停在 `generating` | 后续迭代添加超时重试；MVP 阶段记录到日志并手动处理 |
| T027 文件上传安全 | 恶意文件名、路径穿越 | 使用 UUID 重命名文件，`os.path.join(UPLOAD_DIR, session_id, f"{uuid}.{ext}")` |
| T028 TTS 文件缓存 | 同一 message 重复调用 TTS 应返回缓存文件 | 先检查文件是否存在，存在则直接返回，不存在则调用 OpenAI |

---

### Sprint 6 — 语音与报告 UI（P5 + P6 后段）

> **目标：** Flutter 语音模式 + 报告页面 + 报告 API + 历史记录  
> **任务数：** 5 | **预估工时：** 15–20h  
> **里程碑：** 语音模式端到端可用 + 报告自动轮询展示

| 任务 | 标题 | 依赖 | 预估 | 风险 | 影响文件 |
|------|------|------|------|------|---------|
| T029 | Flutter 语音模式 UI | T024, T027, T028 | 4h | 🔴 高 | `mobile/lib/features/interview/presentation/session/voice/**` |
| T032 | Report API | T031 | 2–3h | 🟢 低 | `backend/app/api/v1/interviews.py` (追加) |
| T033 | Flutter 报告页与轮询 | T024, T032 | 4h | 🟡 中 | `mobile/lib/features/report/**` |
| T035 | Flutter 历史记录页 | T025, T020 | 3–4h | 🟢 低 | `mobile/lib/features/history/**` |
| T036 | Flutter 个人资料页 | T015, T014 | 2–3h | 🟢 低 | `mobile/lib/features/profile/**` |

**⚡ 并行机会：** T029（语音）、T033（报告）、T035（历史）、T036（资料）四条线可完全并行  
**⚠️ Sprint 风险点：**

| 风险 | 说明 | 缓解 |
|------|------|------|
| **T029 录音平台差异** | `record` 包在 iOS/Android 输出格式不同（iOS: .m4a, Android: .webm） | transcribe API 接受多格式；Flutter 侧不硬编码扩展名 |
| **T029 TTS 自动播放时序** | interviewer 消息渲染后立即播放，多条消息可能同时播放 | 仅对**最新** interviewer 消息自动播放；历史消息显示播放按钮但不自动触发 |
| T033 轮询定时器泄漏 | 页面退出后 Timer 继续运行，导致内存泄漏或 setState on disposed | 在 `dispose()` 中 cancel Timer；使用 `Bloc` 的 `StreamSubscription` 管理 |
| T033 报告超时 UX | 2 分钟超时后显示错误，但后台可能仍在生成 | 提示文案："报告生成中，请稍后在历史记录中查看"（PRD RPT-12） |

---

### Sprint 7 — 整合、测试与交付（P7 + P8）

> **目标：** Flutter 全页面整合 + 全部测试 + README + E2E 清单  
> **任务数：** 4 | **预估工时：** 12–16h  
> **里程碑：** MVP 完成，可按 README 从零启动，E2E 清单可执行

| 任务 | 标题 | 依赖 | 预估 | 风险 | 影响文件 |
|------|------|------|------|------|---------|
| T037 | Flutter 整合与主题 | T035, T036, T033, T029 | 4h | 🟡 中 | `mobile/lib/app/app.dart`, `mobile/lib/app/theme.dart`, `mobile/lib/app/di.dart`, `mobile/lib/main.dart` |
| T038 | 后端集成测试 | T026 | 4h | 🟡 中 | `backend/tests/test_auth_api.py`, `backend/tests/test_interview_api.py` |
| T039 | README 文档 | T037, T038 | 2–3h | 🟢 低 | `README.md` |
| T040 | E2E 测试清单 | T039 | 2–3h | 🟢 低 | `docs/E2E_CHECKLIST.md` |

**⚠️ Sprint 风险点：**

| 风险 | 说明 | 缓解 |
|------|------|------|
| T037 GetIt 注册遗漏 | 4 个 feature 的 Repository/Bloc 全部需要注册，遗漏导致运行时 null 异常 | 逐 feature 验证：`GetIt.I<XXXRepository>()` 不抛异常 |
| T038 mock OpenAI 复杂度 | 集成测试需要 mock 全部 OpenAI 调用（start/messages/complete） | `conftest.py` 提供 `mock_openai_service` fixture，返回固定问题/报告 |
| T038 测试数据清理 | 集成测试写入 DB 数据需清理，避免影响后续测试 | 每个测试使用独立事务 + rollback（`pytest` fixture `db_session`） |

---

## 5. 文件冲突全景图

> 标记被 **≥ 3 个任务** 修改的高冲突文件

| 文件 | 修改任务数 | 涉及任务 | 冲突级别 | 解决策略 |
|------|-----------|---------|---------|---------|
| `backend/app/api/v1/interviews.py` | **7** | T020, T021, T022, T023, T027, T028, T032 | 🔴 极高 | 严格按 ID 顺序追加；每个任务在文件末尾追加新 endpoint 函数 |
| `backend/app/services/openai_service.py` | **5** | T017, T018, T027, T028, T030 | 🟡 中 | 每个任务追加新方法，不修改已有方法 |
| `mobile/lib/app/router.dart` | **3** | T016, T033, T037 | 🟡 中 | T016 定义路由框架，T033 追加报告路由，T037 最终整合 |
| `backend/app/api/v1/router.py` | **4** | T012, T014, T015, T020 | 🟢 低 | 每次追加一行 `include_router()` |
| `backend/tests/conftest.py` | **3** | T026, T034, T038 | 🟢 低 | 追加 fixture，不修改已有 |

---

## 6. 风险登记簿

### 6.1 技术风险

| ID | 风险描述 | 影响范围 | 概率 | 影响 | 等级 | 缓解措施 | 涉及任务 |
|----|---------|---------|------|------|------|---------|---------|
| TR-01 | **LLM 输出 `[INTERVIEW_COMPLETE]` 不可靠** | 面试无法正常结束 | 中 | 高 | 🔴 | 代码双重兜底：① 检查 `[INTERVIEW_COMPLETE]` ② `question_count >= max` 强制结束 | T018, T019 |
| TR-02 | **LLM 报告 JSON 输出不稳定** | 报告生成失败率高 | 中 | 高 | 🔴 | `response_format=json_object` + 字段校验 + 失败回退 `report_status=failed` | T030, T031 |
| TR-03 | **asyncio.create_task session 丢失** | 报告永远 `generating` | 高 | 高 | 🔴 | 后台任务创建独立 `AsyncSession`；日志记录异常 | T031 |
| TR-04 | **Flutter AuthInterceptor 死循环** | App 卡死 | 中 | 高 | 🔴 | `/auth/refresh` 路径豁免拦截；refresh 401 时清除 token | T013 |
| TR-05 | **录音格式平台差异** | iOS/Android 语音模式不兼容 | 高 | 中 | 🟡 | transcribe 接受多格式；不硬编码文件扩展名 | T027, T029 |
| TR-06 | **并发提交导致消息 sequence 冲突** | DB UNIQUE 约束报错 | 中 | 中 | 🟡 | `SELECT ... FOR UPDATE` 锁定 session 行 | T022 |
| TR-07 | **Docker volume 数据残留** | 开发环境 DB 状态不一致 | 低 | 低 | 🟢 | `docker-compose down -v` 清理；README 注明 | T001 |

### 6.2 进度风险

| ID | 风险描述 | 影响 | 概率 | 缓解 |
|----|---------|------|------|------|
| SR-01 | **T019（状态机）超时** | 阻塞 T020-T023 + T031（5 个后续任务） | 中 | 提前编写状态转换测试表（12 条用例），边写边测 |
| SR-02 | **T024（Flutter 集成）超时** | 阻塞 T029（语音）和 T033（报告 UI） | 中 | 先实现最简版（无动画、无错误处理），再迭代完善 |
| SR-03 | **OpenAI API Key 不可用/额度不足** | 所有 OpenAI 相关任务无法验收 | 低 | 准备 fallback mock 模式（环境变量 `OPENAI_MOCK=true`） |
| SR-04 | **Flutter `build_runner` 生成代码冲突** | T025/T009 model 生成失败 | 中 | 每次 `build_runner` 前先 `--delete-conflicting-outputs` |

### 6.3 质量风险

| ID | 风险描述 | 影响 | 缓解 |
|----|---------|------|------|
| QR-01 | **camelCase 映射遗漏** | 前端 JSON 解析失败 | T009 逐 Schema 对比 API.md §2；T025 逐 Model 验证 `fromJson` |
| QR-02 | **错误码不一致** | 前端错误提示错误 | 后端使用 `AppException` 统一管理；前端根据 `error.code` 匹配 |
| QR-03 | **Prompt 文件被意外修改** | AI 面试质量下降 | Prompt 文件写入后设为只读（`chmod 444`）；PRD 禁止修改 |

---

## 7. 并行执行策略

### 7.1 双轨并行（推荐）

后端与移动端天然分离，可双轨并行：

```
时间轴 ──────────────────────────────────────────────────────────────▶

Backend:  T001→T002→T003→T006→T007→T009→T010→T011→T012→T014/T015
                                              │
                                              ▼
          T017→T018→T019→T020→T021→T022→T023→T027→T028→T030→T031→T032→T038

Mobile:   T001→T004→T005→T013→T025→T016───────────────────→T024→T029→T033→T035→T036→T037
                                    ↑ 等待后端 API ↑
```

### 7.2 并行窗口

| 时间段 | Backend 执行 | Mobile 执行 | 同步点 |
|--------|-------------|-------------|--------|
| Sprint 1 | T001→T002→T003 | T001→T004 | T001 共享 |
| Sprint 2 | T006→T007→T008→T009 | T005→T013 | 无依赖 |
| Sprint 3 | T010→T011→T012→T017→T018 | T013→T025 | 无依赖 |
| Sprint 4 | T019→T020→T021→T022→T023→T014→T015 | T016 | T014 解锁 T016 |
| Sprint 5 | T026→T027→T028→T030→T031→T034 | T024 | **⚠️ T024 需等 T021/T022/T023** |
| Sprint 6 | T032 | T029→T033→T035→T036 | T032 解锁 T033 |
| Sprint 7 | T038→T039→T040 | T037 | **⚠️ T037 需等 T029/T033/T035/T036** |

### 7.3 同步检查点（必须前后端对齐）

| 检查点 | 时机 | 验证内容 |
|--------|------|---------|
| **CP-1** | Sprint 3 结束 | Auth API ↔ Flutter LoginPage：注册/登录/token 刷新可联调 |
| **CP-2** | Sprint 4 结束 | Interview API ↔ Flutter SetupPage：创建面试→跳转 session 页 |
| **CP-3** | Sprint 5 结束 | Full Interview API ↔ Flutter SessionPage：文字模式 Q&A 端到端 |
| **CP-4** | Sprint 6 结束 | Voice+Report API ↔ Flutter：语音模式 + 报告轮询 |
| **CP-5** | Sprint 7 结束 | 全功能 E2E：按 E2E_CHECKLIST.md 手工验证 |

---

## 8. 每 Sprint 交付物清单

| Sprint | 交付物 | 验收方式 |
|--------|--------|---------|
| S1 | docker-compose 可启动；FastAPI `/health` 200；Flutter 空白 App | `docker-compose up` + `curl /health` + `flutter run` |
| S2 | 6 张 DB 表 + 8 条 seed；ORM + Schema 就绪 | `alembic upgrade head` + `\dt` + 逐表对比 DATABASE.md |
| S3 | Auth 4 端点可用；OpenAI 首题/下一题可调用；Flutter 登录注册 | `curl` 测试 Auth API + `python -c` 测试 OpenAI |
| S4 | 面试 API 7 端点可用；Flutter 设置页+路由 | `pytest` + `curl` 测试 Interview API |
| S5 | 文字面试 Flutter↔Backend 端到端；语音/报告后端就绪 | 手动跑 3 轮 Q&A；`pytest` 单元测试 |
| S6 | 语音模式可用；报告展示；历史/资料页 | 手动跑语音模式；查看报告 UI |
| S7 | MVP 完整；README 可复现；E2E 清单 | 按 README 从零启动；E2E 清单全绿 |

---

## 9. 缓冲与应急

### 9.1 时间缓冲

| Sprint | 预估工时 | 建议预留 | 缓冲比例 |
|--------|---------|---------|---------|
| S1 | 15–20h | 24h | +20% |
| S2 | 12–16h | 20h | +25% |
| S3 | 21–28h | 32h | +15% |
| S4 | 24–32h | 40h | +25% |
| S5 | 21–28h | 36h | +30% ← 风险最密集 |
| S6 | 15–20h | 24h | +20% |
| S7 | 12–16h | 20h | +25% |

### 9.2 应急方案

| 场景 | 应急措施 |
|------|---------|
| T019 状态机超时（> 6h） | 简化为 happy path（pending→in_progress→completed），cancel/failed 路径后续补 |
| T031 报告生成不稳定 | 改为同步生成（complete 接口阻塞等待），牺牲响应速度换取可靠性 |
| T029 语音平台兼容问题 | 降级：仅支持文字模式，语音标记为"Coming Soon" |
| OpenAI API 不可用 | 所有 OpenAI 调用启用 mock 模式（返回固定问题/报告），不影响开发进度 |
| T024 集成超时 | 先用 `http` 包替代 `dio` 做简单联调，确认 API 格式无误后再切回完整实现 |

---

## 10. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-12 | 初始开发计划（基于 TASKS.md v1.0.0） |
