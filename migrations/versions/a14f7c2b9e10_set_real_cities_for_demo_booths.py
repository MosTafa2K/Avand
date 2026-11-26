"""set real cities for demo booths."""

from alembic import op
import sqlalchemy as sa


revision = "a14f7c2b9e10"
down_revision = "8d0d960da81d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE booths
            SET city = CASE slug
                WHEN 'demo-booth-1' THEN 'تهران'
                WHEN 'demo-booth-2' THEN 'مشهد'
                WHEN 'demo-booth-3' THEN 'اصفهان'
                ELSE city
            END
            WHERE slug IN ('demo-booth-1', 'demo-booth-2', 'demo-booth-3')
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE booths
            SET city = 'نامشخص'
            WHERE slug IN ('demo-booth-1', 'demo-booth-2', 'demo-booth-3')
            """
        )
    )
