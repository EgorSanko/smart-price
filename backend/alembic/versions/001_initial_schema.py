"""Initial database schema.

Revision ID: 001_initial
Revises:
Create Date: 2025-01-24

Creates all tables for Smart Price:
- marketplaces
- categories
- products
- price_history
- product_matches
- users
- price_alerts
- search_history
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables."""
    # Enable required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create enums
    alert_type_enum = postgresql.ENUM(
        "below", "drop_percent", "any_change",
        name="alert_type_enum",
        create_type=True,
    )
    alert_type_enum.create(op.get_bind(), checkfirst=True)

    alert_status_enum = postgresql.ENUM(
        "active", "triggered", "expired", "paused",
        name="alert_status_enum",
        create_type=True,
    )
    alert_status_enum.create(op.get_bind(), checkfirst=True)

    # 1. Marketplaces
    op.create_table(
        "marketplaces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False, comment="Short unique name"),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("base_url", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_marketplaces_name", "marketplaces", ["name"])

    # 2. Categories
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    # 3. Products
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("marketplace_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("original_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("images", postgresql.ARRAY(sa.String(1000)), nullable=True),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("specs", postgresql.JSONB(), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("seller_name", sa.String(255), nullable=True),
        sa.Column("seller_rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("barcode", sa.String(50), nullable=True),
        sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["marketplace_id"], ["marketplaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_products_marketplace_id", "products", ["marketplace_id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_is_available", "products", ["is_available"])
    op.create_index("ix_products_barcode", "products", ["barcode"])
    op.create_index(
        "ix_product_marketplace_external",
        "products",
        ["marketplace_id", "external_id"],
        unique=True,
    )
    op.create_index(
        "ix_product_available_price",
        "products",
        ["is_available", "current_price"],
    )
    # GIN index for full-text search (requires pg_trgm extension)
    op.execute(
        """
        CREATE INDEX ix_product_title_gin
        ON products
        USING gin (title gin_trgm_ops)
        """
    )

    # 4. Price History
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("original_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_price_history_product_id", "price_history", ["product_id"])
    op.create_index("ix_price_history_recorded_at", "price_history", ["recorded_at"])
    op.create_index(
        "ix_price_history_product_date",
        "price_history",
        ["product_id", "recorded_at"],
    )

    # 5. Product Matches
    op.create_table(
        "product_matches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("canonical_product_id", sa.Integer(), nullable=False),
        sa.Column("matched_product_id", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("match_method", sa.String(50), nullable=False, server_default="ml"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["canonical_product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("canonical_product_id", "matched_product_id", name="uq_product_match_pair"),
    )
    op.create_index("ix_product_match_canonical", "product_matches", ["canonical_product_id"])
    op.create_index("ix_product_match_matched", "product_matches", ["matched_product_id"])
    op.create_index("ix_product_match_confidence", "product_matches", ["confidence_score"])

    # 6. Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # 7. Price Alerts
    op.create_table(
        "price_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("target_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("alert_type", alert_type_enum, nullable=False, server_default="below"),
        sa.Column("status", alert_status_enum, nullable=False, server_default="active"),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_price_alerts_user_id", "price_alerts", ["user_id"])
    op.create_index("ix_price_alerts_product_id", "price_alerts", ["product_id"])
    op.create_index("ix_price_alerts_status", "price_alerts", ["status"])
    op.create_index("ix_price_alert_active", "price_alerts", ["status", "product_id"])
    op.create_index("ix_price_alert_user_status", "price_alerts", ["user_id", "status"])

    # 8. Search History
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("query", sa.String(500), nullable=False),
        sa.Column("filters", postgresql.JSONB(), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("clicked_product_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["clicked_product_id"], ["products.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_search_history_user_id", "search_history", ["user_id"])
    op.create_index("ix_search_history_session_id", "search_history", ["session_id"])
    op.create_index("ix_search_history_created_at", "search_history", ["created_at"])
    op.create_index(
        "ix_search_history_user_created",
        "search_history",
        ["user_id", "created_at"],
    )

    # Insert default marketplaces
    op.execute(
        """
        INSERT INTO marketplaces (name, display_name, base_url, is_active) VALUES
        ('ozon', 'Ozon', 'https://www.ozon.ru', true),
        ('wildberries', 'Wildberries', 'https://www.wildberries.ru', true),
        ('yandex_market', 'Яндекс Маркет', 'https://market.yandex.ru', true),
        ('aliexpress', 'AliExpress', 'https://aliexpress.ru', false)
        """
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("search_history")
    op.drop_table("price_alerts")
    op.drop_table("users")
    op.drop_table("product_matches")
    op.drop_table("price_history")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("marketplaces")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS alert_status_enum")
    op.execute("DROP TYPE IF EXISTS alert_type_enum")

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
