"""add today serving tables

Revision ID: 20260617_0004
Revises: 20260613_0003
Create Date: 2026-06-17
"""

from alembic import op

revision = "20260617_0004"
down_revision = "20260613_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        create table if not exists serving_pages (
            page_id varchar(80) primary key,
            page_type varchar(50) not null,
            page_date date not null,
            market varchar(20) not null,
            user_id varchar(100) not null default '',
            title varchar(300),
            status varchar(30) not null default 'ready',
            payload jsonb not null default '{}'::jsonb,
            generated_at timestamptz not null default now(),
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        )
        """
    )
    op.execute("alter table serving_pages add column if not exists page_type varchar(50) not null default 'today'")
    op.execute("alter table serving_pages add column if not exists page_date date")
    op.execute("alter table serving_pages add column if not exists market varchar(20) not null default 'KR'")
    op.execute("alter table serving_pages add column if not exists user_id varchar(100) not null default ''")
    op.execute("alter table serving_pages add column if not exists title varchar(300)")
    op.execute("alter table serving_pages add column if not exists status varchar(30) not null default 'ready'")
    op.execute("alter table serving_pages add column if not exists payload jsonb not null default '{}'::jsonb")
    op.execute("alter table serving_pages add column if not exists generated_at timestamptz not null default now()")
    op.execute("alter table serving_pages add column if not exists created_at timestamptz not null default now()")
    op.execute("alter table serving_pages add column if not exists updated_at timestamptz not null default now()")
    op.execute(
        """
        create index if not exists idx_serving_pages_today_lookup
            on serving_pages (page_type, page_date, market, user_id, generated_at desc)
        """
    )

    op.execute(
        """
        create table if not exists documents (
            doc_id varchar(120) primary key,
            title varchar(500) not null,
            source_type varchar(50),
            source_name varchar(200),
            source_url text,
            summary_kr text,
            raw_text text,
            published_at timestamptz,
            metadata jsonb,
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        )
        """
    )
    op.execute("alter table documents add column if not exists title varchar(500)")
    op.execute("alter table documents add column if not exists source_type varchar(50)")
    op.execute("alter table documents add column if not exists source_name varchar(200)")
    op.execute("alter table documents add column if not exists source_url text")
    op.execute("alter table documents add column if not exists summary_kr text")
    op.execute("alter table documents add column if not exists raw_text text")
    op.execute("alter table documents add column if not exists published_at timestamptz")
    op.execute("alter table documents add column if not exists metadata jsonb")
    op.execute("alter table documents add column if not exists created_at timestamptz not null default now()")
    op.execute("alter table documents add column if not exists updated_at timestamptz not null default now()")
    op.execute("create index if not exists idx_documents_published_at on documents (published_at)")

    op.execute(
        """
        create table if not exists document_chunks (
            chunk_id varchar(120) primary key,
            doc_id varchar(120) not null references documents (doc_id) on delete cascade,
            chunk_index integer,
            text text not null,
            metadata jsonb,
            created_at timestamptz not null default now()
        )
        """
    )
    op.execute("alter table document_chunks add column if not exists doc_id varchar(120)")
    op.execute("alter table document_chunks add column if not exists chunk_index integer")
    op.execute("alter table document_chunks add column if not exists text text")
    op.execute("alter table document_chunks add column if not exists metadata jsonb")
    op.execute("alter table document_chunks add column if not exists created_at timestamptz not null default now()")
    op.execute("create index if not exists idx_document_chunks_doc_id on document_chunks (doc_id, chunk_index)")

    op.execute(
        """
        create table if not exists evidence_links (
            id bigserial primary key,
            target_type varchar(50) not null,
            target_id varchar(120) not null,
            section_key varchar(80),
            doc_id varchar(120) references documents (doc_id) on delete set null,
            chunk_id varchar(120) references document_chunks (chunk_id) on delete set null,
            final_rank integer,
            score numeric(12, 8),
            metadata jsonb,
            created_at timestamptz not null default now()
        )
        """
    )
    op.execute("alter table evidence_links add column if not exists target_type varchar(50)")
    op.execute("alter table evidence_links add column if not exists target_id varchar(120)")
    op.execute("alter table evidence_links add column if not exists section_key varchar(80)")
    op.execute("alter table evidence_links add column if not exists doc_id varchar(120)")
    op.execute("alter table evidence_links add column if not exists chunk_id varchar(120)")
    op.execute("alter table evidence_links add column if not exists final_rank integer")
    op.execute("alter table evidence_links add column if not exists score numeric(12, 8)")
    op.execute("alter table evidence_links add column if not exists metadata jsonb")
    op.execute("alter table evidence_links add column if not exists created_at timestamptz not null default now()")
    op.execute(
        """
        create index if not exists idx_evidence_links_target
            on evidence_links (target_type, target_id, section_key, final_rank)
        """
    )


def downgrade() -> None:
    op.execute("drop table if exists evidence_links cascade")
    op.execute("drop table if exists document_chunks cascade")
    op.execute("drop table if exists documents cascade")
    op.execute("drop table if exists serving_pages cascade")
