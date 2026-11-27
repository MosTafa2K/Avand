"""add indexes for the high-traffic product listing paths."""

from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "e7f9a1b2c304"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_products_active_created_at",
        "products",
        ["is_active", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_products_active_booth_created_at",
        "products",
        ["is_active", "booth_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_order_items_product_order",
        "order_items",
        ["product_id", "order_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_order_items_product_order", table_name="order_items")
    op.drop_index("ix_products_active_booth_created_at", table_name="products")
    op.drop_index("ix_products_active_created_at", table_name="products")
