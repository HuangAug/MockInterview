"""Seed job_roles with 8 preset positions.

Revision ID: 007
Revises: 006
Create Date: 2026-06-12

"""
from collections.abc import Sequence

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEED_ROWS = [
    (
        "a1000001-0000-4000-8000-000000000001",
        "frontend",
        "前端工程师",
        "Frontend Engineer",
        "负责 Web 前端开发，包括 HTML/CSS/JavaScript、React/Vue 等框架、性能优化和用户体验。",
        1,
    ),
    (
        "a1000001-0000-4000-8000-000000000002",
        "backend",
        "后端工程师",
        "Backend Engineer",
        "负责服务端开发，包括 API 设计、数据库、微服务、高并发和高可用架构。",
        2,
    ),
    (
        "a1000001-0000-4000-8000-000000000003",
        "fullstack",
        "全栈工程师",
        "Full Stack Engineer",
        "同时负责前端和后端开发，具备全链路开发和系统设计能力。",
        3,
    ),
    (
        "a1000001-0000-4000-8000-000000000004",
        "mobile",
        "移动端工程师",
        "Mobile Engineer",
        "负责 iOS/Android 原生或跨平台移动应用开发，包括 Flutter/React Native。",
        4,
    ),
    (
        "a1000001-0000-4000-8000-000000000005",
        "product",
        "产品经理",
        "Product Manager",
        "负责产品规划、需求分析、用户研究和跨团队协调，推动产品从 0 到 1。",
        5,
    ),
    (
        "a1000001-0000-4000-8000-000000000006",
        "data_analyst",
        "数据分析师",
        "Data Analyst",
        "负责数据收集、清洗、分析和可视化，为业务决策提供数据支持。",
        6,
    ),
    (
        "a1000001-0000-4000-8000-000000000007",
        "algorithm",
        "算法工程师",
        "Algorithm Engineer",
        "负责机器学习/深度学习算法研发、模型训练优化和 AI 系统落地。",
        7,
    ),
    (
        "a1000001-0000-4000-8000-000000000008",
        "test_engineer",
        "测试工程师",
        "Test Engineer",
        "负责软件测试策略、自动化测试、质量保障和缺陷管理。",
        8,
    ),
]


def upgrade() -> None:
    cols = "id, code, name_zh, name_en, description, sort_order, is_active"
    for row in SEED_ROWS:
        values = (
            f"'{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', {row[5]}, true"
        )
        op.execute(f"INSERT INTO job_roles ({cols}) VALUES ({values})")


def downgrade() -> None:
    ids = ", ".join(f"'{row[0]}'" for row in SEED_ROWS)
    op.execute(f"DELETE FROM job_roles WHERE id IN ({ids})")
