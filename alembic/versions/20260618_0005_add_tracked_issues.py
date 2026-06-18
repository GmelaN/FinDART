"""add tracked issues

Revision ID: 20260618_0005
Revises: 20260617_0004
Create Date: 2026-06-18
"""

from alembic import op

revision = "20260618_0005"
down_revision = "20260617_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        create table if not exists tracked_issues (
            id bigserial primary key,
            user_id varchar(100) not null default '',
            market varchar(20) not null default 'KR',
            subscription_key varchar(200) not null,
            issue jsonb not null default '{}'::jsonb,
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now(),
            constraint uq_tracked_issues_user_market_key unique (user_id, market, subscription_key)
        )
        """
    )
    op.execute("alter table tracked_issues add column if not exists user_id varchar(100) not null default ''")
    op.execute("alter table tracked_issues add column if not exists market varchar(20) not null default 'KR'")
    op.execute("alter table tracked_issues add column if not exists subscription_key varchar(200)")
    op.execute("alter table tracked_issues add column if not exists issue jsonb not null default '{}'::jsonb")
    op.execute("alter table tracked_issues add column if not exists created_at timestamptz not null default now()")
    op.execute("alter table tracked_issues add column if not exists updated_at timestamptz not null default now()")
    op.execute(
        """
        create unique index if not exists uq_tracked_issues_user_market_key
            on tracked_issues (user_id, market, subscription_key)
        """
    )


def downgrade() -> None:
    op.execute("drop table if exists tracked_issues cascade")
