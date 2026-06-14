# MockInterview AI — 编码规范

> 版本：1.0.2  
> 最后更新：2026-06-13  
> 适用范围：backend/ 与 mobile/ 全部代码

---

## 1. 通用规范

### 1.1 语言与注释

| 项 | 规范 |
|----|------|
| 代码标识符 | 英文 |
| 代码注释 | 英文，仅解释非 obvious 逻辑 |
| UI 文案 | 简体中文（硬编码在 Flutter 页面或 constants 文件） |
| Git commit message | 英文，格式：`type(scope): description` |
| Git 分支 | `feature/sprint-{n}-{slug}`，如 `feature/sprint-1-infrastructure` |
| Git Push / PR | 每个 TASK 仅 Commit；Sprint 全部 TASK 完成后 Push 并创建 PR |

### 1.2 Git 工作流

| 时机 | 操作 |
|------|------|
| 开始 Sprint 前 | `git fetch origin` → `git checkout main` → `git pull origin main`，确认与 `origin/main` 一致 |
| 开始 Sprint | 从已同步的 main 创建分支 `feature/sprint-{n}-{slug}` |
| 每个 TASK 完成 | Commit（格式见 §1.1），更新任务状态 |
| Sprint 全部 TASK 完成 | 执行验证 → `git push origin` 当前分支 → 创建 PR |

**禁止：**

- 从未同步的本地 main 创建 Sprint 分支
- 从上一 Sprint 的 feature 分支直接延续开发（除非用户明确要求）
- 在前一 Sprint 的 PR 尚未合并时开始下一 Sprint（除非用户确认）
- 为单个 TASK 创建独立分支
- TASK 完成后 Push 或创建 PR
- Push 到 `main` / `master`

PR 必须包含：功能说明、修改文件、测试结果、风险分析、对应 Sprint、包含任务。

完整规则见 [CLAUDE.md](../CLAUDE.md)。

### 1.3 Commit Type

| type | 用途 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| refactor | 重构（无功能变更） |
| test | 测试 |
| docs | 文档 |
| chore | 构建/工具 |

### 1.4 禁止事项（全局）

- **禁止**实现 PRD Out of Scope 中的功能
- **禁止**修改 API.md 中的字段名、路径、错误码
- **禁止**修改 DATABASE.md 中的表名、字段名、约束
- **禁止**修改 ARCHITECTURE.md 中 Prompt 模板的语义
- **禁止**硬编码密钥（OpenAI Key, JWT Secret 等）
- **禁止**在日志中输出 password、token 明文
- **禁止**跳过 TASKS.md 中的任务顺序

---

## 2. Python / FastAPI 规范

### 2.1 版本与工具

| 工具 | 版本/配置 |
|------|----------|
| Python | 3.11+ |
| 格式化 | Ruff format |
| Lint | Ruff check |
| 类型检查 | mypy（strict mode 推荐） |

### 2.2 目录与分层

```
Router (api/v1/) → Service (services/) → Model (models/)
```

| 层 | 职责 | 禁止 |
|----|------|------|
| Router | 参数校验、调用 Service、返回 Response | 业务逻辑、直接 DB 操作 |
| Service | 业务逻辑、状态机、调用 OpenAI | HTTP 相关代码 |
| Model | SQLAlchemy ORM 定义 | 业务逻辑 |
| Schema | Pydantic 请求/响应 DTO | 业务逻辑 |

### 2.3 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | snake_case | `interview_service.py` |
| 类名 | PascalCase | `InterviewService` |
| 函数/变量 | snake_case | `create_session()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_QUESTIONS = 8` |
| DB 字段 | snake_case | `question_count` |
| API JSON 字段 | camelCase | `questionCount` |

### 2.4 Pydantic Schema 规范

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class InterviewSessionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    id: UUID
    job_role_id: UUID
    question_count: int
    # API 输出为 jobRoleId, questionCount
```

- 所有 Response Schema 必须使用 camelCase alias
- Request Schema 接受 camelCase 输入（`populate_by_name=True`）

### 2.5 异常处理

```python
# backend/app/core/exceptions.py
class AppException(Exception):
    def __init__(
        self,
        code: int,
        message: str,
        details: list[dict] | None = None,
        status_code: int = 400,
    ):
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
```

- Service 层抛 `AppException`，禁止抛裸 `HTTPException`
- Router 层不 catch AppException（由全局 handler 处理）
- 未捕获异常 → 50001

### 2.6 异步规范

- 所有 DB 操作使用 async SQLAlchemy session
- 所有 OpenAI 调用使用 async client
- 报告生成使用 `asyncio.create_task()`，不阻塞 HTTP 响应

### 2.7 依赖注入

```python
# backend/app/api/deps.py
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    ...

async def get_interview_service(
    db: AsyncSession = Depends(get_db),
) -> InterviewService:
    return InterviewService(db)
```

### 2.8 测试规范

| 类型 | 工具 | 位置 |
|------|------|------|
| 单元测试 | pytest + pytest-asyncio | `backend/tests/test_*_service.py` |
| API 集成测试 | pytest + httpx AsyncClient | `backend/tests/test_*_api.py` |
| Mock | unittest.mock / pytest-mock | mock OpenAI 调用 |

- 测试文件命名：`test_{module}.py`
- 测试函数命名：`test_{scenario}_{expected}`
- OpenAI 调用必须 mock，单元测试不得调用真实 API

### 2.9 环境变量

- 通过 `pydantic-settings` 的 `Settings` 类读取
- 必填项无默认值，缺失时启动失败
- `.env.example` 同步更新

---

## 3. Flutter / Dart 规范

### 3.1 版本与工具

| 工具 | 配置 |
|------|------|
| Flutter | 3.x stable |
| Dart | 3.x |
| 分析 | `flutter analyze` 零 error |
| 格式化 | `dart format .` |

### 3.2 目录结构（Feature-First）

```
features/{feature_name}/
├── data/
│   ├── models/           # freezed + json_serializable
│   ├── repositories/     # API 调用
│   └── datasources/      # 可选 remote/local
├── domain/               # 可选 entities
└── presentation/
    ├── bloc/             # flutter_bloc
    ├── pages/
    └── widgets/
```

### 3.3 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | snake_case | `interview_session_page.dart` |
| 类名 | PascalCase | `InterviewSessionPage` |
| 变量/函数 | lowerCamelCase | `questionCount` |
| 常量 | lowerCamelCase 或 k前缀 | `kMaxQuestions` |
| 私有 | _前缀 | `_submitAnswer()` |

### 3.4 状态管理（flutter_bloc）

```dart
// Event
sealed class InterviewEvent {}
class StartInterview extends InterviewEvent {
  final String sessionId;
  StartInterview(this.sessionId);
}

// State
sealed class InterviewState {}
class InterviewInitial extends InterviewState {}
class InterviewLoading extends InterviewState {}
class InterviewActive extends InterviewState {
  final InterviewSession session;
  final List<Message> messages;
  InterviewActive({required this.session, required this.messages});
}
class InterviewError extends InterviewState {
  final String message;
  InterviewError(this.message);
}
```

- 每个 feature 一个 Bloc（或 Cubit）
- Bloc 不直接依赖 Dio，通过 Repository 调用 API
- UI 文案错误提示使用 API 返回的 message

### 3.5 Model 规范（freezed + json_serializable）

```dart
@freezed
class InterviewSession with _$InterviewSession {
  const factory InterviewSession({
    required String id,
    required String jobRoleId,
    required String difficulty,
    required int questionCount,
    required int maxQuestions,
    required String status,
    required String reportStatus,
    @Default([]) List<Message> messages,
  }) = _InterviewSession;

  factory InterviewSession.fromJson(Map<String, dynamic> json) =>
      _$InterviewSessionFromJson(json);
}
```

- 所有 API Response Model 必须与 API.md §2 字段一致
- 运行 `dart run build_runner build --delete-conflicting-outputs` 生成代码

### 3.6 网络层

```dart
// Dio 配置
final dio = Dio(BaseOptions(
  baseUrl: ApiConstants.baseUrl,
  connectTimeout: const Duration(seconds: 10),
  receiveTimeout: const Duration(seconds: 180), // 后端 OpenAI 调用超时 60s + 重试 2 次，最坏 ~180s
  headers: {'Content-Type': 'application/json'},
));
```

- AuthInterceptor：401 时自动 refresh token 并重试
- 统一解析 `{success, data, error}` 响应结构
- API 错误抛 ApiException

### 3.7 路由（go_router）

```dart
GoRoute(
  path: '/interview/session/:id',
  builder: (context, state) => InterviewSessionPage(
    sessionId: state.pathParameters['id']!,
  ),
),
```

- 路由 path 与 PRD §6.1 完全一致
- 认证 redirect：无 token 时跳转 /login

### 3.8 UI 规范

| 项 | 规范 |
|----|------|
| 主色 | #2563EB |
| 背景 | #F8FAFC |
| 错误色 | #EF4444 |
| 成功色 | #22C55E |
| 警告色 | #F59E0B |
| 信息色 | #3B82F6 |
| 字体 | 系统默认（不引入自定义字体） |
| 间距 | 8 的倍数（8, 16, 24, 32） |
| 圆角 | 卡片 12, 按钮 8 |

- 使用 Material 3
- 加载状态显示 CircularProgressIndicator
- 错误使用 SnackBar 或 Dialog

### 3.9 安全存储

- Access Token / Refresh Token 存 `flutter_secure_storage`
- 禁止存 SharedPreferences

---

## 4. API 与 DB 一致性检查清单

开发时逐项核对：

- [ ] API Request 字段名 camelCase 与 API.md 一致
- [ ] API Response 字段名 camelCase 与 API.md 一致
- [ ] DB 字段 snake_case 与 DATABASE.md 一致
- [ ] 枚举值与 PRD/DATABASE 定义一致
- [ ] 错误码与 API.md §1.5 一致
- [ ] Prompt 文件与 ARCHITECTURE §6 verbatim 一致

---

## 5. Code Review 自检清单

每个任务完成前：

- [ ] 无 hardcoded secrets
- [ ] 无 console.log / print 调试语句
- [ ] 无 TODO/FIXME 遗留（除非 TASKS 明确要求）
- [ ] 新增 Service 有对应单元测试
- [ ] flutter analyze / ruff check 无 error
- [ ] 验收标准全部满足

---

## 6. 文件头模板

### Python

```python
"""Interview service — business logic for interview sessions."""
```

### Dart

```dart
/// Interview session page — displays Q&A chat interface.
```

---

## 7. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-12 | 初始版本 |
| 1.0.1 | 2026-06-12 | §1.1–1.2 Git 工作流改为 Sprint 级 Push/PR |
| 1.0.2 | 2026-06-13 | §1.2 新增 Sprint 开始前同步 main 流程 |
