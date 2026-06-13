"""initial schema

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01
"""

from alembic import op

revision = "20260601_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    with open("docs/schema.sql", encoding="utf-8") as schema_file:
        statements = [statement.strip() for statement in schema_file.read().split(";") if statement.strip()]
    for statement in statements:
        bind.exec_driver_sql(statement)


def downgrade() -> None:
    op.execute(
        """
        drop table if exists risk_assessments cascade;
        drop table if exists metric_values cascade;
        drop table if exists metric_snapshots cascade;
        drop table if exists metric_definitions cascade;
        drop table if exists corporate_events cascade;
        drop table if exists daily_prices cascade;
        drop table if exists account_aliases cascade;
        drop table if exists financial_statement_items cascade;
        drop table if exists standard_accounts cascade;
        drop table if exists financial_statements cascade;
        drop table if exists dart_filings cascade;
        drop table if exists company_listings cascade;
        drop table if exists companies cascade;
        """
    )
