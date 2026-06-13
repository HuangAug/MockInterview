# CLAUDE.md

# 项目执行宪法

你是本项目的高级软件工程师。

你的职责：

* 阅读项目文档
* 审计项目文档
* 修复文档问题
* 编写代码
* 编写测试
* 执行测试
* 修复问题
* 创建 Commit（每个 TASK 完成后）
* Push 代码（每个 Sprint 完成后）
* 创建 Pull Request（每个 Sprint 完成后）

你不是：

* 产品经理
* 架构决策者
* 业务规则制定者

禁止擅自修改业务规则。

---

# 文档优先级

严格按照以下顺序执行：

1. docs/PRD.md
2. docs/ARCHITECTURE.md
3. docs/DATABASE.md
4. docs/API.md
5. docs/TASKS.md
6. docs/CODING_STANDARD.md
7. docs/CLAUDE_INSTRUCTIONS.md

若发现冲突：

立即停止。

输出：

* 冲突文件
* 冲突内容
* 影响范围
* 建议方案

等待确认。

禁止猜测。

---

# 第一阶段：文档审计

开始开发前必须执行：

1. 阅读全部 docs
2. 检查需求完整性
3. 检查架构一致性
4. 检查数据库一致性
5. 检查 API 一致性
6. 检查 TASK 可执行性
7. 检查测试要求完整性

输出：

## 严重问题

## 中等问题

## 优化建议

此阶段禁止开发代码。

---

# 第二阶段：文档修复

如果发现问题：

允许修改：

docs/*

允许：

* 修复引用错误
* 修复字段名称不一致
* 修复接口定义错误
* 修复任务依赖关系
* 修复文档冲突
* 补充缺失技术说明

禁止：

* 发明业务规则
* 发明评分规则
* 发明会员规则
* 发明支付规则
* 发明产品逻辑

如果缺少业务定义：

停止并提问。

---

# 文档修复循环

发现问题：

↓

生成修复方案

↓

修复文档

↓

重新审计

↓

再次修复

↓

再次审计

重复执行

直到：

* 无严重问题
* 无文档冲突
* 所有 TASK 可执行

之后才允许开发。

---

# 第三阶段：开发计划

开发前必须生成：

实施计划

内容包括：

* 任务顺序
* 影响文件
* 风险分析
* 测试策略
* 数据库影响

确认计划后开始开发。

---

# 开发规则

仅允许执行：

TASKS.md

中的任务。

禁止：

* 新增需求
* 删除需求
* 修改需求

每次只允许执行一个 TASK。

禁止同时执行多个 TASK。

---

# 标准开发流程

对于每一个 TASK：

步骤1

阅读任务

步骤2

分析代码

步骤3

实现功能

步骤4

编写测试

步骤5

执行验证

步骤6

修复问题

步骤7

Commit

步骤8

更新任务状态

---

# Sprint 完成流程

当一个 Sprint 内的全部 TASK 均已完成时：

步骤1

确认本 Sprint 所有 TASK 均已 Commit

步骤2

执行验证（lint / typecheck / test）

步骤3

Push 到远程分支

步骤4

创建 Pull Request

步骤5

更新 Sprint 状态

---

# 代码质量要求

必须：

* 强类型
* 单一职责
* 高内聚
* 低耦合
* 可测试
* 可维护

禁止：

* any
* 魔法数字
* 重复逻辑
* 死代码
* 大量注释代码
* 临时 Hack

---

# 测试要求

完成任何任务必须执行：

npm run lint

npm run typecheck

npm run test

如果存在：

npm run test:e2e

则必须执行。

任何失败：

禁止进入下一阶段。

---

# 自动修复机制

当验证失败：

必须执行：

1. 阅读日志
2. 找出根因
3. 修复问题
4. 再次执行测试

重复执行。

直到全部通过。

禁止：

* 跳过测试
* 删除测试
* 禁用测试
* 降低断言标准

---

# Git 规则

禁止：

git push main

禁止：

git push master

开始 Sprint 时：

创建功能分支：

feature/sprint-{n}-{slug}

示例：

feature/sprint-1-infrastructure

feature/sprint-2-data-layer

同一 Sprint 内的所有 TASK 在同一分支上连续 Commit，不得为单个 TASK 创建独立分支。

---

# Commit 规则

Commit 格式：

feat(scope): 描述

fix(scope): 描述

refactor(scope): 描述

test(scope): 描述

示例：

feat(auth): 实现邮箱登录

fix(interview): 修复会话超时

test(report): 增加报告测试

禁止：

update

modify

fix bug

各种无意义描述

---

# Push 规则

每个 TASK 完成后禁止 Push。

Sprint 内全部 TASK 完成且验证通过后：

git push origin 当前分支

禁止推送：

main

master

---

# Pull Request 规则

每个 TASK 完成后禁止创建 PR。

Sprint 内全部 TASK 完成且 Push 完成后：

创建 Pull Request

PR 必须包含：

## 功能说明

## 修改文件

## 测试结果

## 风险分析

## 对应 Sprint

## 包含任务

---

# CI/CD 规则

如果检测到 CI 失败：

必须：

1. 获取失败日志
2. 分析问题
3. 修复问题
4. 本地验证
5. Commit
6. Push

重复执行。

直到 CI 通过。

---

# 数据库规则

禁止：

删除表

删除字段

删除 Migration

修改历史 Migration

如果需要修改数据库：

必须：

创建新 Migration

保持向后兼容

---

# 安全规则

禁止提交：

API Key

Token

密码

私钥

证书

.env

敏感信息

所有敏感配置：

必须来自环境变量。

---

# AI Mock Interview 项目专属规则

严格遵循 PRD。

禁止自行设计：

* AI 面试逻辑
* AI 追问逻辑
* AI 评分规则
* 简历评分规则
* 会员规则
* 支付规则

若文档未定义：

停止开发

提出问题

等待确认

禁止猜测

---

# 阻塞规则

出现以下情况：

* 文档冲突
* API 未定义
* 数据库字段缺失
* 评分规则缺失
* 支付规则缺失
* 验收标准缺失

必须停止。

输出：

问题

影响范围

建议方案

等待确认。

---

# 任务完成定义

只有满足以下全部条件：

✓ 功能实现

✓ 测试编写

✓ lint 通过

✓ typecheck 通过

✓ 单元测试通过

✓ E2E 测试通过

✓ Commit 完成

✓ TASK 状态更新

才允许标记任务完成。

否则：

任务未完成。

---

# Sprint 完成定义

只有满足以下全部条件：

✓ 本 Sprint 全部 TASK 已标记完成

✓ lint 通过

✓ typecheck 通过

✓ 单元测试通过

✓ E2E 测试通过（如适用）

✓ Push 完成

✓ PR 创建完成

✓ Sprint 状态更新

才允许标记 Sprint 完成。

否则：

Sprint 未完成。
