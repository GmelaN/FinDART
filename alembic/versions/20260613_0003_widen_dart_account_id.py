"""widen dart account id columns

Revision ID: 20260613_0003
Revises: 20260613_0002
Create Date: 2026-06-13
"""

from alembic import op

revision = "20260613_0003"
down_revision = "20260613_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("alter table financial_statement_items alter column dart_account_id type varchar(300)")
    op.execute("alter table account_aliases alter column dart_account_id type varchar(300)")


def downgrade() -> None:
    op.execute("alter table financial_statement_items alter column dart_account_id type varchar(100)")
    op.execute("alter table account_aliases alter column dart_account_id type varchar(100)")
