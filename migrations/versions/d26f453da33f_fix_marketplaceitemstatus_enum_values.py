"""Fix marketplaceitemstatus enum values by replacing the enum type

Revision ID: d26f453da33f
Revises: e19e72c93202
Create Date: 2025-07-09 09:09:39.959777

"""

from alembic import op
import sqlalchemy as sa

revision = 'd26f453da33f'
down_revision = 'e19e72c93202'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create the new enum type with corrected values
    op.execute("CREATE TYPE marketplaceitemstatus_new AS ENUM ('AVAILABLE', 'SOLD_PENDING', 'SOLD_OUT', 'CANCELLED')")

    # 2. Alter the column to use the new enum type with corrected value mapping
    op.execute("""
        ALTER TABLE marketplace_listings
        ALTER COLUMN status
        TYPE marketplaceitemstatus_new
        USING
            CASE status
                WHEN 'SOLD_PENDIN.' THEN 'SOLD_PENDING'::text::marketplaceitemstatus_new
                ELSE status::text::marketplaceitemstatus_new
            END
    """)

    # 3. Rename old enum type to temporary name
    op.execute("ALTER TYPE marketplaceitemstatus RENAME TO marketplaceitemstatus_old")

    # 4. Rename new enum type to original enum name
    op.execute("ALTER TYPE marketplaceitemstatus_new RENAME TO marketplaceitemstatus")

    # 5. Drop old enum type
    op.execute("DROP TYPE marketplaceitemstatus_old")


def downgrade():
    # 1. Create old enum type with typo
    op.execute("CREATE TYPE marketplaceitemstatus_old AS ENUM ('AVAILABLE', 'SOLD_PENDIN.', 'SOLD_OUT', 'CANCELLED')")

    # 2. Alter column to use old enum type, mapping corrected value back to typo
    op.execute("""
        ALTER TABLE marketplace_listings
        ALTER COLUMN status
        TYPE marketplaceitemstatus_old
        USING
            CASE status
                WHEN 'SOLD_PENDING' THEN 'SOLD_PENDIN.'::text::marketplaceitemstatus_old
                ELSE status::text::marketplaceitemstatus_old
            END
    """)

    # 3. Rename current enum type to temporary name
    op.execute("ALTER TYPE marketplaceitemstatus RENAME TO marketplaceitemstatus_new")

    # 4. Rename old enum type back to original enum name
    op.execute("ALTER TYPE marketplaceitemstatus_old RENAME TO marketplaceitemstatus")

    # 5. Drop temporary enum type
    op.execute("DROP TYPE marketplaceitemstatus_new")
