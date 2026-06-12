# MockInterview AI — 数据库设计文档

> 版本：1.0.0  
> 最后更新：2026-06-12  
> 数据库：PostgreSQL 15  
> 关联文档：[ARCHITECTURE.md](./ARCHITECTURE.md) | [API.md](./API.md)

---

## 1. 设计原则

- 主键统一使用 UUID（`gen_random_uuid()`）
- 时间字段统一 `TIMESTAMPTZ`，UTC 存储
- 枚举值使用 `VARCHAR + CHECK` 约束，不使用 PostgreSQL ENUM 类型
- 表名、字段名：`snake_case`
- 软删除：`users.deleted_at`（MVP 仅用户表）
- 外键删除策略见各表说明

---

## 2. ER 图

```mermaid
erDiagram
    users ||--o{ refresh_tokens : has
    users ||--o{ interview_sessions : creates
    users }o--|| job_roles : targets
    job_roles ||--o{ interview_sessions : for
    interview_sessions ||--o{ interview_messages : contains
    interview_sessions ||--o| interview_reports : generates

    users {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar display_name
        uuid target_job_role_id FK
        varchar avatar_url
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }

    refresh_tokens {
        uuid id PK
        uuid user_id FK
        varchar token_hash
        timestamptz expires_at
        timestamptz revoked_at
        timestamptz created_at
    }

    job_roles {
        uuid id PK
        varchar code UK
        varchar name_zh
        varchar name_en
        text description
        int sort_order
        boolean is_active
    }

    interview_sessions {
        uuid id PK
        uuid user_id FK
        uuid job_role_id FK
        varchar difficulty
        varchar mode
        varchar status
        int question_count
        int max_questions
        varchar report_status
        timestamptz started_at
        timestamptz ended_at
        timestamptz created_at
        timestamptz updated_at
    }

    interview_messages {
        uuid id PK
        uuid session_id FK
        varchar role
        text content
        varchar audio_url
        int sequence
        timestamptz created_at
    }

    interview_reports {
        uuid id PK
        uuid session_id FK UK
        numeric overall_score
        numeric communication_score
        numeric technical_score
        numeric problem_solving_score
        numeric structure_score
        jsonb strengths
        jsonb weaknesses
        jsonb suggestions
        jsonb question_feedback
        text summary
        timestamptz created_at
    }
```

---

## 3. 枚举值定义

### 3.1 difficulty（interview_sessions.difficulty）

| 值 | 含义 |
|----|------|
| `junior` | 初级 |
| `mid` | 中级 |
| `senior` | 高级 |

### 3.2 mode（interview_sessions.mode）

| 值 | 含义 |
|----|------|
| `text` | 文字模式 |
| `voice` | 语音模式 |

### 3.3 status（interview_sessions.status）

| 值 | 含义 |
|----|------|
| `pending` | 待开始 |
| `in_progress` | 进行中 |
| `completed` | 已完成 |
| `cancelled` | 已取消 |
| `failed` | 失败 |

### 3.4 report_status（interview_sessions.report_status）

| 值 | 含义 |
|----|------|
| `pending` | 未生成 |
| `generating` | 生成中 |
| `ready` | 已就绪 |
| `failed` | 生成失败 |

### 3.5 role（interview_messages.role）

| 值 | 含义 |
|----|------|
| `interviewer` | AI 面试官 |
| `candidate` | 候选人（用户） |

---

## 4. 表结构详细定义

### 4.1 users

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 用户 ID |
| email | VARCHAR(255) | NOT NULL | — | 登录邮箱（未删除用户唯一，见下方索引） |
| password_hash | VARCHAR(255) | NOT NULL | — | bcrypt 哈希 |
| display_name | VARCHAR(50) | NOT NULL | — | 昵称 |
| target_job_role_id | UUID | NULL, FK → job_roles(id) ON DELETE SET NULL | NULL | 目标岗位 |
| avatar_url | VARCHAR(500) | NULL | NULL | 头像 URL（MVP 不用） |
| created_at | TIMESTAMPTZ | NOT NULL | now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | 更新时间 |
| deleted_at | TIMESTAMPTZ | NULL | NULL | 软删除时间 |

**索引：**
- `uq_users_email_active` ON (email) UNIQUE WHERE deleted_at IS NULL

**业务约束：**
- 查询用户时必须加 `WHERE deleted_at IS NULL`
- email 在未删除用户中唯一（通过部分唯一索引 `uq_users_email_active` 实现）

---

### 4.2 refresh_tokens

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | Token ID |
| user_id | UUID | NOT NULL, FK → users(id) ON DELETE CASCADE | — | 所属用户 |
| token_hash | VARCHAR(255) | NOT NULL | — | SHA-256(refresh_token) |
| expires_at | TIMESTAMPTZ | NOT NULL | — | 过期时间 |
| revoked_at | TIMESTAMPTZ | NULL | NULL | 吊销时间 |
| created_at | TIMESTAMPTZ | NOT NULL | now() | 创建时间 |

**索引：**
- `idx_refresh_tokens_user_id` ON (user_id)
- `idx_refresh_tokens_token_hash` ON (token_hash)

**业务约束：**
- 有效 token：`revoked_at IS NULL AND expires_at > now()`

---

### 4.3 job_roles

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 岗位 ID |
| code | VARCHAR(50) | NOT NULL, UNIQUE | — | 岗位代码 |
| name_zh | VARCHAR(100) | NOT NULL | — | 中文名 |
| name_en | VARCHAR(100) | NOT NULL | — | 英文名 |
| description | TEXT | NULL | NULL | 岗位描述 |
| sort_order | INT | NOT NULL | — | 排序 |
| is_active | BOOLEAN | NOT NULL | true | 是否启用 |

**索引：**
- `idx_job_roles_sort_order` ON (sort_order) WHERE is_active = true

---

### 4.4 interview_sessions

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 会话 ID |
| user_id | UUID | NOT NULL, FK → users(id) ON DELETE CASCADE | — | 用户 ID |
| job_role_id | UUID | NOT NULL, FK → job_roles(id) ON DELETE RESTRICT | — | 岗位 ID |
| difficulty | VARCHAR(20) | NOT NULL, CHECK | — | junior/mid/senior |
| mode | VARCHAR(20) | NOT NULL, CHECK | — | text/voice |
| status | VARCHAR(20) | NOT NULL, CHECK, DEFAULT 'pending' | pending | 会话状态 |
| question_count | INT | NOT NULL, DEFAULT 0, CHECK (>= 0) | 0 | 已出题目数 |
| max_questions | INT | NOT NULL, DEFAULT 8, CHECK (> 0) | 8 | 最大题数 |
| report_status | VARCHAR(20) | NOT NULL, CHECK, DEFAULT 'pending' | pending | 报告状态 |
| started_at | TIMESTAMPTZ | NULL | NULL | 开始时间 |
| ended_at | TIMESTAMPTZ | NULL | NULL | 结束时间 |
| created_at | TIMESTAMPTZ | NOT NULL | now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL | now() | 更新时间 |

**CHECK 约束：**
```sql
CONSTRAINT chk_sessions_difficulty CHECK (difficulty IN ('junior', 'mid', 'senior'))
CONSTRAINT chk_sessions_mode CHECK (mode IN ('text', 'voice'))
CONSTRAINT chk_sessions_status CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled', 'failed'))
CONSTRAINT chk_sessions_report_status CHECK (report_status IN ('pending', 'generating', 'ready', 'failed'))
```

**索引：**
- `idx_sessions_user_created` ON (user_id, created_at DESC)
- `idx_sessions_status` ON (status)
- `idx_sessions_user_status` ON (user_id, status)

---

### 4.5 interview_messages

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 消息 ID |
| session_id | UUID | NOT NULL, FK → interview_sessions(id) ON DELETE CASCADE | — | 会话 ID |
| role | VARCHAR(20) | NOT NULL, CHECK | — | interviewer/candidate |
| content | TEXT | NOT NULL | — | 消息内容 |
| audio_url | VARCHAR(500) | NULL | NULL | 语音文件 URL（candidate 语音回答；MVP 阶段不写入，预留扩展） |
| sequence | INT | NOT NULL, CHECK (> 0) | — | 序号，从 1 开始 |
| created_at | TIMESTAMPTZ | NOT NULL | now() | 创建时间 |

**CHECK 约束：**
```sql
CONSTRAINT chk_messages_role CHECK (role IN ('interviewer', 'candidate'))
```

**唯一约束：**
```sql
CONSTRAINT uq_messages_session_sequence UNIQUE (session_id, sequence)
```

**索引：**
- `idx_messages_session_sequence` ON (session_id, sequence)

---

### 4.6 interview_reports

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | UUID | PRIMARY KEY | gen_random_uuid() | 报告 ID |
| session_id | UUID | NOT NULL, UNIQUE, FK → interview_sessions(id) ON DELETE CASCADE | — | 会话 ID |
| overall_score | NUMERIC(5,2) | NOT NULL, CHECK (>= 0 AND <= 100) | — | 综合得分 |
| communication_score | NUMERIC(5,2) | NOT NULL, CHECK (>= 0 AND <= 100) | — | 表达得分 |
| technical_score | NUMERIC(5,2) | NOT NULL, CHECK (>= 0 AND <= 100) | — | 技术得分 |
| problem_solving_score | NUMERIC(5,2) | NOT NULL, CHECK (>= 0 AND <= 100) | — | 问题解决得分 |
| structure_score | NUMERIC(5,2) | NOT NULL, CHECK (>= 0 AND <= 100) | — | 结构得分 |
| strengths | JSONB | NOT NULL | — | 优点数组 |
| weaknesses | JSONB | NOT NULL | — | 不足数组 |
| suggestions | JSONB | NOT NULL | — | 建议数组 |
| question_feedback | JSONB | NOT NULL | — | 逐题反馈 |
| summary | TEXT | NOT NULL | — | 总结 |
| created_at | TIMESTAMPTZ | NOT NULL | now() | 创建时间 |

**JSONB 结构：**

```json
// strengths / weaknesses / suggestions
["字符串1", "字符串2"]

// question_feedback
[
  {
    "sequence": 1,
    "question": "请介绍一下你自己",
    "answerSummary": "候选人介绍了自己的教育背景和项目经验",
    "score": 75.00,
    "feedback": "自我介绍结构清晰，但缺乏量化成果"
  }
]
```

**索引：**
- `idx_reports_session_id` ON (session_id)

---

## 5. 完整 DDL

```sql
-- Migration: 001_initial_schema
-- 执行前确保 CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. job_roles（无外键依赖，最先创建）
CREATE TABLE job_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    name_zh VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT uq_job_roles_code UNIQUE (code)
);

CREATE INDEX idx_job_roles_sort_order ON job_roles (sort_order) WHERE is_active = true;

-- 2. users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    target_job_role_id UUID REFERENCES job_roles(id) ON DELETE SET NULL,
    avatar_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT uq_users_email_active UNIQUE (email) WHERE deleted_at IS NULL
);

-- 3. refresh_tokens
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);

-- 4. interview_sessions
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_role_id UUID NOT NULL REFERENCES job_roles(id) ON DELETE RESTRICT,
    difficulty VARCHAR(20) NOT NULL,
    mode VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    question_count INT NOT NULL DEFAULT 0,
    max_questions INT NOT NULL DEFAULT 8,
    report_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_sessions_difficulty CHECK (difficulty IN ('junior', 'mid', 'senior')),
    CONSTRAINT chk_sessions_mode CHECK (mode IN ('text', 'voice')),
    CONSTRAINT chk_sessions_status CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled', 'failed')),
    CONSTRAINT chk_sessions_report_status CHECK (report_status IN ('pending', 'generating', 'ready', 'failed')),
    CONSTRAINT chk_sessions_question_count CHECK (question_count >= 0),
    CONSTRAINT chk_sessions_max_questions CHECK (max_questions > 0)
);

CREATE INDEX idx_sessions_user_created ON interview_sessions (user_id, created_at DESC);
CREATE INDEX idx_sessions_status ON interview_sessions (status);
CREATE INDEX idx_sessions_user_status ON interview_sessions (user_id, status);

-- 5. interview_messages
CREATE TABLE interview_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    audio_url VARCHAR(500),
    sequence INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_messages_role CHECK (role IN ('interviewer', 'candidate')),
    CONSTRAINT chk_messages_sequence CHECK (sequence > 0),
    CONSTRAINT uq_messages_session_sequence UNIQUE (session_id, sequence)
);

CREATE INDEX idx_messages_session_sequence ON interview_messages (session_id, sequence);

-- 6. interview_reports
CREATE TABLE interview_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    overall_score NUMERIC(5,2) NOT NULL,
    communication_score NUMERIC(5,2) NOT NULL,
    technical_score NUMERIC(5,2) NOT NULL,
    problem_solving_score NUMERIC(5,2) NOT NULL,
    structure_score NUMERIC(5,2) NOT NULL,
    strengths JSONB NOT NULL,
    weaknesses JSONB NOT NULL,
    suggestions JSONB NOT NULL,
    question_feedback JSONB NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_reports_session_id UNIQUE (session_id),
    CONSTRAINT chk_reports_overall_score CHECK (overall_score >= 0 AND overall_score <= 100),
    CONSTRAINT chk_reports_communication_score CHECK (communication_score >= 0 AND communication_score <= 100),
    CONSTRAINT chk_reports_technical_score CHECK (technical_score >= 0 AND technical_score <= 100),
    CONSTRAINT chk_reports_problem_solving_score CHECK (problem_solving_score >= 0 AND problem_solving_score <= 100),
    CONSTRAINT chk_reports_structure_score CHECK (structure_score >= 0 AND structure_score <= 100)
);

CREATE INDEX idx_reports_session_id ON interview_reports (session_id);
```

---

## 6. Alembic 迁移顺序

| 顺序 | Migration 文件 | 内容 |
|------|---------------|------|
| 001 | `001_create_job_roles.py` | 创建 job_roles 表 |
| 002 | `002_create_users.py` | 创建 users 表 |
| 003 | `003_create_refresh_tokens.py` | 创建 refresh_tokens 表 |
| 004 | `004_create_interview_sessions.py` | 创建 interview_sessions 表 |
| 005 | `005_create_interview_messages.py` | 创建 interview_messages 表 |
| 006 | `006_create_interview_reports.py` | 创建 interview_reports 表 |
| 007 | `007_seed_job_roles.py` | 插入 8 条岗位种子数据 |

---

## 7. 种子数据

### 7.1 job_roles 种子 SQL

```sql
-- Migration: 007_seed_job_roles
-- 使用固定 UUID 便于测试引用

INSERT INTO job_roles (id, code, name_zh, name_en, description, sort_order, is_active) VALUES
(
    'a1000001-0000-4000-8000-000000000001',
    'frontend',
    '前端工程师',
    'Frontend Engineer',
    '负责 Web 前端开发，包括 HTML/CSS/JavaScript、React/Vue 等框架、性能优化和用户体验。',
    1,
    true
),
(
    'a1000001-0000-4000-8000-000000000002',
    'backend',
    '后端工程师',
    'Backend Engineer',
    '负责服务端开发，包括 API 设计、数据库、微服务、高并发和高可用架构。',
    2,
    true
),
(
    'a1000001-0000-4000-8000-000000000003',
    'fullstack',
    '全栈工程师',
    'Full Stack Engineer',
    '同时负责前端和后端开发，具备全链路开发和系统设计能力。',
    3,
    true
),
(
    'a1000001-0000-4000-8000-000000000004',
    'mobile',
    '移动端工程师',
    'Mobile Engineer',
    '负责 iOS/Android 原生或跨平台移动应用开发，包括 Flutter/React Native。',
    4,
    true
),
(
    'a1000001-0000-4000-8000-000000000005',
    'product',
    '产品经理',
    'Product Manager',
    '负责产品规划、需求分析、用户研究和跨团队协调，推动产品从 0 到 1。',
    5,
    true
),
(
    'a1000001-0000-4000-8000-000000000006',
    'data_analyst',
    '数据分析师',
    'Data Analyst',
    '负责数据收集、清洗、分析和可视化，为业务决策提供数据支持。',
    6,
    true
),
(
    'a1000001-0000-4000-8000-000000000007',
    'algorithm',
    '算法工程师',
    'Algorithm Engineer',
    '负责机器学习/深度学习算法研发、模型训练优化和 AI 系统落地。',
    7,
    true
),
(
    'a1000001-0000-4000-8000-000000000008',
    'test_engineer',
    '测试工程师',
    'Test Engineer',
    '负责软件测试策略、自动化测试、质量保障和缺陷管理。',
    8,
    true
);
```

---

## 8. SQLAlchemy Model 映射要点

| Model 类 | 表名 | 关系 |
|----------|------|------|
| `User` | users | `refresh_tokens` one-to-many; `interview_sessions` one-to-many; `target_job_role` many-to-one |
| `RefreshToken` | refresh_tokens | `user` many-to-one |
| `JobRole` | job_roles | — |
| `InterviewSession` | interview_sessions | `user`, `job_role` many-to-one; `messages` one-to-many; `report` one-to-one |
| `InterviewMessage` | interview_messages | `session` many-to-one |
| `InterviewReport` | interview_reports | `session` one-to-one |

**updated_at 自动更新：** 使用 SQLAlchemy `onupdate=func.now()` 或在 Service 层显式设置。

---

## 9. 常用查询示例

### 9.1 用户历史面试列表（分页）

```sql
SELECT
    s.id,
    s.difficulty,
    s.mode,
    s.status,
    s.question_count,
    s.report_status,
    s.created_at,
    jr.name_zh AS job_role_name,
    r.overall_score
FROM interview_sessions s
JOIN job_roles jr ON s.job_role_id = jr.id
LEFT JOIN interview_reports r ON r.session_id = s.id
WHERE s.user_id = :user_id
ORDER BY s.created_at DESC
LIMIT :page_size OFFSET :offset;
```

### 9.2 会话详情含消息

```sql
SELECT m.*
FROM interview_messages m
WHERE m.session_id = :session_id
ORDER BY m.sequence ASC;
```

---

## 10. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-12 | 初始版本 |
