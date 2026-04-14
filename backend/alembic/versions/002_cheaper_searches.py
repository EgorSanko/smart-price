"""Add cheaper_searches table for "Найти дешевле" feature.

Revision ID: 002_cheaper
Revises: 001_initial
Create Date: 2026-04-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_cheaper"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    cheaper_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed", "cancelled",
        name="cheaper_status_enum",
        create_type=True,
    )
    cheaper_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "cheaper_searches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=False), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("orig_domain", sa.String(length=200), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="cheaper_status_enum", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("product_name", sa.Text(), nullable=True),
        sa.Column("product_img_url", sa.String(length=1000), nullable=True),
        sa.Column("orig_price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True, server_default="RUR"),
        sa.Column("planned_shops", postgresql.JSONB(), nullable=True),
        sa.Column("offers", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cheaper_searches_task_id", "cheaper_searches", ["task_id"], unique=True)
    op.create_index("ix_cheaper_searches_user_id", "cheaper_searches", ["user_id"])
    op.create_index("ix_cheaper_searches_user_created", "cheaper_searches", ["user_id", "created_at"])
    op.create_index("ix_cheaper_searches_status", "cheaper_searches", ["status"])


def downgrade() -> None:
    op.drop_index("ix_cheaper_searches_status", table_name="cheaper_searches")
    op.drop_index("ix_cheaper_searches_user_created", table_name="cheaper_searches")
    op.drop_index("ix_cheaper_searches_user_id", table_name="cheaper_searches")
    op.drop_index("ix_cheaper_searches_task_id", table_name="cheaper_searches")
    op.drop_table("cheaper_searches")
    postgresql.ENUM(name="cheaper_status_enum").drop(op.get_bind(), checkfirst=True)
