"""add indexes for product filters and order listing."""

from alembic import op

revision = "e7f9a1b2c304"
down_revision = "d4e8f6a1b203"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_booths_city", "booths", ["city"], unique=False)
    op.create_index("ix_products_active_price", "products", ["is_active", "price"], unique=False)
    op.create_index("ix_orders_user_created_at", "orders", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_orders_user_created_at", table_name="orders")
    op.drop_index("ix_products_active_price", table_name="products")
    op.drop_index("ix_booths_city", table_name="booths")
