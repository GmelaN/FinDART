"""remove collection runtime tables

Revision ID: 20260613_0002
Revises: 20260601_0001
Create Date: 2026-06-13
"""

from alembic import op

revision = "20260613_0002"
down_revision = "20260601_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("drop table if exists collection_schedules cascade")
    op.execute("drop table if exists data_collection_jobs cascade")


def downgrade() -> None:
    op.execute(
        """
        create table data_collection_jobs (
            id bigserial primary key,
            job_id varchar(40) not null unique,
            job_type varchar(50) not null,
            status varchar(30) not null default 'QUEUED',
            requested_by varchar(100),
            market varchar(20) not null default 'KOSPI',
            params jsonb not null default '{}'::jsonb,
            progress jsonb not null default '{}'::jsonb,
            error jsonb,
            parent_job_id bigint references data_collection_jobs (id) on delete set null,
            enqueue_recalculation boolean not null default true,
            created_at timestamptz not null default now(),
            queued_at timestamptz not null default now(),
            started_at timestamptz,
            finished_at timestamptz
        )
        """
    )
    op.execute("create index idx_data_collection_jobs_status_created on data_collection_jobs (status, created_at)")
    op.execute("create index idx_data_collection_jobs_type_created on data_collection_jobs (job_type, created_at)")
    op.execute("create index idx_data_collection_jobs_parent on data_collection_jobs (parent_job_id)")
    op.execute(
        """
        create table collection_schedules (
            id bigserial primary key,
            schedule_code varchar(80) not null unique,
            job_type varchar(50) not null,
            market varchar(20) not null default 'KOSPI',
            recommended_interval varchar(30) not null,
            is_active boolean not null default true,
            params jsonb not null default '{}'::jsonb,
            last_success_job_id bigint references data_collection_jobs (id) on delete set null,
            last_success_at timestamptz,
            next_recommended_at timestamptz,
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        )
        """
    )
    op.execute("create index idx_collection_schedules_active_next on collection_schedules (is_active, next_recommended_at)")
