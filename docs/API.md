# MockInterview AI — API 接口文档

> 版本：1.0.0  
> 最后更新：2026-06-12  
> Base URL：`/api/v1`  
> 关联文档：[PRD.md](./PRD.md) | [DATABASE.md](./DATABASE.md) | [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 1. 通用规范

### 1.1 协议与格式

| 项 | 规范 |
|----|------|
| 协议 | HTTPS（生产）/ HTTP（开发） |
| 编码 | UTF-8 |
| 请求 Content-Type | `application/json`（除文件上传为 `multipart/form-data`） |
| 响应 Content-Type | `application/json` |
| 日期时间 | ISO 8601 UTC，如 `2026-06-12T10:30:00Z` |
| JSON 字段命名 | **camelCase** |

### 1.2 认证

需认证端点在 Header 中携带：

```
Authorization: Bearer {accessToken}
```

### 1.3 统一响应结构

**成功响应：**

```json
{
  "success": true,
  "data": { ... },
  "message": null
}
```

**分页成功响应：**

```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 100,
      "totalPages": 5
    }
  },
  "message": null
}
```

**错误响应：**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": 40001,
    "message": "参数校验失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      }
    ]
  }
}
```

### 1.4 HTTP 状态码映射

| HTTP Status | 场景 |
|-------------|------|
| 200 | 成功 GET/PATCH/POST（非创建） |
| 201 | 成功 POST 创建资源 |
| 400 | 参数校验失败 |
| 401 | 未认证 / Token 无效 |
| 403 | 无权访问 |
| 404 | 资源不存在 |
| 409 | 状态冲突 / 重复资源 |
| 500 | 服务器内部错误 |
| 502 | 外部服务（OpenAI）错误 |

### 1.5 错误码表

| code | HTTP | message（默认） | 场景 |
|------|------|----------------|------|
| 40001 | 400 | 参数校验失败 | Pydantic 校验失败 |
| 40002 | 400 | 密码不符合要求 | 密码规则不满足 |
| 40003 | 400 | 文件大小超出限制 | 音频 > 25MB |
| 40004 | 400 | 不支持的文件格式 | 音频格式非法 |
| 40101 | 401 | 未认证 | 缺少或无效 Token |
| 40102 | 401 | 邮箱或密码错误 | 登录失败 |
| 40103 | 401 | Refresh Token 无效或已过期 | refresh 失败 |
| 40301 | 403 | 无权访问该资源 | 非本人 session |
| 40401 | 404 | 资源不存在 | 通用 404 |
| 40402 | 404 | 岗位不存在 | jobRoleId 无效 |
| 40403 | 404 | 面试会话不存在 | sessionId 无效 |
| 40404 | 404 | 报告不存在或尚未生成 | report 未 ready |
| 40901 | 409 | 操作与当前状态冲突 | 如 completed 后再 submit |
| 40902 | 409 | 邮箱已被注册 | 重复注册 |
| 40903 | 409 | 面试会话状态不允许此操作 | 如 pending 时 submit |
| 50001 | 500 | 服务器内部错误 | 未捕获异常 |
| 50201 | 502 | AI 服务暂时不可用 | OpenAI 调用失败 |

---

## 2. 公共 Schema 定义

### 2.1 TokenResponse

```json
{
  "accessToken": "string, JWT",
  "refreshToken": "string, 128-char hex",
  "tokenType": "Bearer",
  "expiresIn": 900
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| accessToken | string | JWT Access Token |
| refreshToken | string | Refresh Token 明文（仅返回一次，128 hex 字符） |
| tokenType | string | 固定 `"Bearer"` |
| expiresIn | integer | Access Token 有效期（秒），固定 900 |

### 2.2 UserResponse

```json
{
  "id": "uuid",
  "email": "string",
  "displayName": "string",
  "targetJobRoleId": "uuid | null",
  "targetJobRoleName": "string | null",
  "avatarUrl": "string | null",
  "createdAt": "datetime"
}
```

### 2.3 JobRoleResponse

```json
{
  "id": "uuid",
  "code": "string",
  "nameZh": "string",
  "nameEn": "string",
  "description": "string | null",
  "sortOrder": "integer"
}
```

### 2.4 MessageResponse

```json
{
  "id": "uuid",
  "sessionId": "uuid",
  "role": "interviewer | candidate",
  "content": "string",
  "audioUrl": "string | null",
  "sequence": "integer",
  "createdAt": "datetime"
}
```

### 2.5 InterviewSessionResponse

```json
{
  "id": "uuid",
  "jobRoleId": "uuid",
  "jobRoleName": "string",
  "difficulty": "junior | mid | senior",
  "mode": "text | voice",
  "status": "pending | in_progress | completed | cancelled | failed",
  "questionCount": "integer",
  "maxQuestions": "integer",
  "reportStatus": "pending | generating | ready | failed",
  "startedAt": "datetime | null",
  "endedAt": "datetime | null",
  "createdAt": "datetime",
  "updatedAt": "datetime",
  "messages": ["MessageResponse"] 
}
```

> 列表接口不含 `messages` 字段；详情接口含。

### 2.6 InterviewSessionListItem

```json
{
  "id": "uuid",
  "jobRoleName": "string",
  "difficulty": "junior | mid | senior",
  "mode": "text | voice",
  "status": "string",
  "questionCount": "integer",
  "reportStatus": "string",
  "overallScore": "number | null",
  "createdAt": "datetime"
}
```

### 2.7 QuestionFeedbackItem

```json
{
  "sequence": "integer",
  "question": "string",
  "answerSummary": "string",
  "score": "number",
  "feedback": "string"
}
```

### 2.8 ReportResponse

```json
{
  "id": "uuid",
  "sessionId": "uuid",
  "overallScore": "number",
  "communicationScore": "number",
  "technicalScore": "number",
  "problemSolvingScore": "number",
  "structureScore": "number",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "suggestions": ["string"],
  "questionFeedback": ["QuestionFeedbackItem"],
  "summary": "string",
  "createdAt": "datetime"
}
```

### 2.9 ReportStatusResponse

```json
{
  "sessionId": "uuid",
  "reportStatus": "pending | generating | ready | failed"
}
```

### 2.10 PaginationQuery

| 参数 | 类型 | 默认 | 约束 |
|------|------|------|------|
| page | integer | 1 | >= 1 |
| pageSize | integer | 20 | 1-50 |

> **注意：** 所有列表接口（含非分页接口）统一使用 `{ items: [...] }` 包装。GET /job-roles 为非分页列表，仍使用 items 包装但不含 pagination 对象。

---

## 3. 端点详细定义

---

### 3.1 POST /auth/register

**描述：** 用户注册  
**认证：** 否

**Request Body：**

```json
{
  "email": "user@example.com",
  "password": "Pass1234",
  "displayName": "张三"
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| email | string | 是 | 合法邮箱，max 255 |
| password | string | 是 | 8-64 字符，含字母+数字 |
| displayName | string | 是 | 1-50 字符 |

**Response 201：**

```json
{
  "success": true,
  "data": {
    "user": { /* UserResponse */ },
    "tokens": { /* TokenResponse */ }
  },
  "message": "注册成功"
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40001 | email/displayName 格式错误 |
| 40002 | 密码不符合规则 |
| 40902 | 邮箱已注册 |

**curl 示例：**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Pass1234","displayName":"测试用户"}'
```

---

### 3.2 POST /auth/login

**描述：** 用户登录  
**认证：** 否

**Request Body：**

```json
{
  "email": "user@example.com",
  "password": "Pass1234"
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| email | string | 是 | 合法邮箱 |
| password | string | 是 | 非空 |

**Response 200：**

```json
{
  "success": true,
  "data": {
    "user": { /* UserResponse */ },
    "tokens": { /* TokenResponse */ }
  },
  "message": null
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40001 | 参数缺失 |
| 40102 | 邮箱或密码错误 |

---

### 3.3 POST /auth/refresh

**描述：** 刷新 Token（Rotation）  
**认证：** 否

**Request Body：**

```json
{
  "refreshToken": "a1b2c3d4..."
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| refreshToken | string | 是 | 128 字符 hex |

**Response 200：**

```json
{
  "success": true,
  "data": { /* TokenResponse */ },
  "message": null
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40103 | refresh token 无效/过期/已吊销 |

---

### 3.4 POST /auth/logout

**描述：** 退出登录，吊销 refresh token  
**认证：** 是

**Request Body：**

```json
{
  "refreshToken": "a1b2c3d4..."
}
```

**Response 200：**

```json
{
  "success": true,
  "data": null,
  "message": "已退出登录"
}
```

---

### 3.5 GET /users/me

**描述：** 获取当前用户信息  
**认证：** 是

**Response 200：**

```json
{
  "success": true,
  "data": { /* UserResponse */ },
  "message": null
}
```

---

### 3.6 PATCH /users/me

**描述：** 更新当前用户资料  
**认证：** 是

**Request Body（至少一个字段）：**

```json
{
  "displayName": "新昵称",
  "targetJobRoleId": "a1000001-0000-4000-8000-000000000001"
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| displayName | string | 否 | 1-50 字符 |
| targetJobRoleId | string (uuid) | 否 | 有效 job_role UUID 或 null |

**Response 200：**

```json
{
  "success": true,
  "data": { /* UserResponse */ },
  "message": "更新成功"
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40001 | displayName 格式错误 |
| 40402 | targetJobRoleId 不存在 |

---

### 3.7 GET /job-roles

**描述：** 获取岗位列表  
**认证：** 是

**Response 200：**

```json
{
  "success": true,
  "data": {
    "items": [ /* JobRoleResponse[] */ ]
  },
  "message": null
}
```

---

### 3.8 POST /interviews

**描述：** 创建面试会话  
**认证：** 是

**Request Body：**

```json
{
  "jobRoleId": "a1000001-0000-4000-8000-000000000001",
  "difficulty": "mid",
  "mode": "text"
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| jobRoleId | string (uuid) | 是 | 有效且 is_active 的 job_role |
| difficulty | string | 是 | `junior` \| `mid` \| `senior` |
| mode | string | 是 | `text` \| `voice` |

**Response 201：**

```json
{
  "success": true,
  "data": { /* InterviewSessionResponse, 无 messages */ },
  "message": "面试会话已创建"
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40001 | difficulty/mode 枚举非法 |
| 40402 | jobRoleId 不存在或未激活 |

---

### 3.9 GET /interviews

**描述：** 获取当前用户面试历史（分页）  
**认证：** 是

**Query Parameters：**

| 参数 | 类型 | 默认 | 约束 |
|------|------|------|------|
| page | integer | 1 | >= 1 |
| pageSize | integer | 20 | 1-50 |
| status | string | null | 可选过滤：pending/in_progress/completed/cancelled/failed |

**Response 200：**

```json
{
  "success": true,
  "data": {
    "items": [ /* InterviewSessionListItem[] */ ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 5,
      "totalPages": 1
    }
  },
  "message": null
}
```

---

### 3.10 GET /interviews/{id}

**描述：** 获取面试会话详情（含全部 messages）  
**认证：** 是

**Path Parameters：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | uuid | 会话 ID |

**Response 200：**

```json
{
  "success": true,
  "data": { /* InterviewSessionResponse 含 messages 按 sequence 升序 */ },
  "message": null
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40403 | 会话不存在 |
| 40301 | 非本人会话 |

---

### 3.11 POST /interviews/{id}/start

**描述：** 开始面试，AI 生成第一个问题  
**认证：** 是

**Path Parameters：** `id` (uuid)

**Request Body：** 无

**业务逻辑：**
1. 校验 session.status == `pending`
2. 校验 session.user_id == current_user.id
3. 调用 OpenAI 生成第一题
4. INSERT message (role=interviewer, sequence=1)
5. UPDATE status=in_progress, question_count=1, started_at=now()

**Response 200：**

```json
{
  "success": true,
  "data": {
    "session": { /* InterviewSessionResponse */ },
    "question": { /* MessageResponse, role=interviewer, sequence=1 */ }
  },
  "message": null
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40403 | 会话不存在 |
| 40301 | 非本人 |
| 40903 | status != pending |
| 50201 | OpenAI 失败 |

---

### 3.12 POST /interviews/{id}/messages

**描述：** 提交用户回答，获取 AI 下一题或结束标志  
**认证：** 是

**Path Parameters：** `id` (uuid)

**Request Body：**

```json
{
  "content": "我叫张三，毕业于北京大学计算机系..."
}
```

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| content | string | 是 | 1-5000 字符 |

**业务逻辑：**
1. 校验 status == `in_progress`
2. 计算 next_sequence = 当前 max(sequence) + 1
3. INSERT candidate message (sequence=next_sequence)
4. 若 question_count >= max_questions → isFinished=true, nextQuestion=null
5. 否则调用 OpenAI 生成下一题
6. 若 LLM 返回 [INTERVIEW_COMPLETE] 或 question_count 达到 max → isFinished=true
7. 否则 INSERT interviewer message, question_count++

**Response 200：**

```json
{
  "success": true,
  "data": {
    "answer": { /* MessageResponse, role=candidate */ },
    "nextQuestion": { /* MessageResponse | null */ },
    "isFinished": false,
    "questionCount": 2
  },
  "message": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| answer | MessageResponse | 刚提交的 candidate 消息 |
| nextQuestion | MessageResponse \| null | 下一题；isFinished=true 时为 null |
| isFinished | boolean | 是否应结束面试 |
| questionCount | integer | 当前已出题目数 |

**Errors：**

| code | 条件 |
|------|------|
| 40001 | content 为空或超长 |
| 40403 | 会话不存在 |
| 40301 | 非本人 |
| 40901 | status != in_progress |
| 50201 | OpenAI 失败 |

---

### 3.13 POST /interviews/{id}/complete

**描述：** 主动结束面试，触发报告生成  
**认证：** 是

**Path Parameters：** `id` (uuid)

**Request Body：** 无

**业务逻辑：**
1. 校验 status == `in_progress`
2. 校验 question_count >= 1（否则应使用 cancel）
3. UPDATE status=completed, ended_at=now(), report_status=generating
4. 触发后台 asyncio task 生成报告

**Response 200：**

```json
{
  "success": true,
  "data": {
    "session": { /* InterviewSessionResponse, status=completed, reportStatus=generating */ }
  },
  "message": "面试已结束，正在生成报告"
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40903 | status != in_progress |
| 40901 | question_count == 0（应使用 cancel） |

---

### 3.14 POST /interviews/{id}/cancel

**描述：** 取消面试（通常 0 题时退出）  
**认证：** 是

**Path Parameters：** `id` (uuid)

**Request Body：** 无

**业务逻辑：**
1. 校验 status IN (`pending`, `in_progress`)
2. 若 status=in_progress 且 question_count > 0，返回 40901（应使用 complete）
3. UPDATE status=cancelled, ended_at=now()

**Response 200：**

```json
{
  "success": true,
  "data": {
    "session": { /* InterviewSessionResponse, status=cancelled */ }
  },
  "message": "面试已取消"
}
```

---

### 3.15 POST /interviews/{id}/transcribe

**描述：** 上传音频并转写为文本  
**认证：** 是

**Content-Type：** `multipart/form-data`

**Form Fields：**

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| audio | file | 是 | webm/mp3/mp4/m4a/wav, max 25MB |

**业务逻辑：**
1. 校验 session 属于当前用户且 status == `in_progress`
2. 保存音频至 `uploads/audio/{session_id}/{uuid}.ext`
3. 调用 Whisper API (language=zh)
4. 返回转写文本

**Response 200：**

```json
{
  "success": true,
  "data": {
    "text": "转写后的文本内容",
    "audioUrl": "/api/v1/interviews/{id}/audio/{filename}"
  },
  "message": null
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40003 | 文件 > 25MB |
| 40004 | 格式不支持 |
| 40901 | status != in_progress |
| 50201 | Whisper 失败 |

---

### 3.16 GET /interviews/{id}/report

**描述：** 获取面试报告  
**认证：** 是

**Path Parameters：** `id` (uuid)

**业务逻辑：**
1. 校验 session 属于当前用户
2. 校验 report_status == `ready`
3. 返回 interview_reports 记录

**Response 200：**

```json
{
  "success": true,
  "data": { /* ReportResponse */ },
  "message": null
}
```

**Errors：**

| code | 条件 |
|------|------|
| 40403 | 会话不存在 |
| 40404 | report_status != ready |
| 40301 | 非本人 |

---

### 3.17 GET /interviews/{id}/report/status

**描述：** 轮询报告生成状态  
**认证：** 是

**Path Parameters：** `id` (uuid)

**Response 200：**

```json
{
  "success": true,
  "data": { /* ReportStatusResponse */ },
  "message": null
}
```

---

### 3.18 GET /interviews/{id}/messages/{messageId}/tts

**描述：** 获取 AI 问题的 TTS 音频（语音模式）  
**认证：** 是

**Path Parameters：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | uuid | 会话 ID |
| messageId | uuid | interviewer 消息 ID |

**业务逻辑：**
1. 校验 message.role == `interviewer`
2. 校验 session.mode == `voice`
3. 若 TTS 文件不存在，调用 OpenAI TTS 生成并缓存
4. 返回 `audio/mpeg` 二进制流

**Response 200：**

- Content-Type: `audio/mpeg`
- Body: mp3 binary

**Errors：**

| code | 条件 |
|------|------|
| 40403 | 会话/消息不存在 |
| 40901 | message 非 interviewer 或 mode 非 voice |

---

### 3.19 GET /health

**描述：** 健康检查  
**认证：** 否

**Response 200：**

```json
{
  "status": "ok",
  "timestamp": "2026-06-12T10:00:00Z"
}
```

---

## 4. 难度与模式枚举（API 层校验）

```python
# backend/app/schemas/interview.py 中必须使用的 Literal 类型
Difficulty = Literal["junior", "mid", "senior"]
InterviewMode = Literal["text", "voice"]
SessionStatus = Literal["pending", "in_progress", "completed", "cancelled", "failed"]
ReportStatus = Literal["pending", "generating", "ready", "failed"]
MessageRole = Literal["interviewer", "candidate"]
```

---

## 5. 端点汇总表

| # | Method | Path | Auth | 说明 |
|---|--------|------|------|------|
| 1 | POST | /auth/register | 否 | 注册 |
| 2 | POST | /auth/login | 否 | 登录 |
| 3 | POST | /auth/refresh | 否 | 刷新 Token |
| 4 | POST | /auth/logout | 是 | 退出 |
| 5 | GET | /users/me | 是 | 当前用户 |
| 6 | PATCH | /users/me | 是 | 更新资料 |
| 7 | GET | /job-roles | 是 | 岗位列表 |
| 8 | POST | /interviews | 是 | 创建会话 |
| 9 | GET | /interviews | 是 | 历史列表 |
| 10 | GET | /interviews/{id} | 是 | 会话详情 |
| 11 | POST | /interviews/{id}/start | 是 | 开始面试 |
| 12 | POST | /interviews/{id}/messages | 是 | 提交回答 |
| 13 | POST | /interviews/{id}/complete | 是 | 结束面试 |
| 14 | POST | /interviews/{id}/cancel | 是 | 取消面试 |
| 15 | POST | /interviews/{id}/transcribe | 是 | 音频转写 |
| 16 | GET | /interviews/{id}/report | 是 | 获取报告 |
| 17 | GET | /interviews/{id}/report/status | 是 | 报告状态 |
| 18 | GET | /interviews/{id}/messages/{messageId}/tts | 是 | TTS 音频 |
| 19 | GET | /health | 否 | 健康检查 |

---

## 6. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-12 | 初始版本 |
