create table companies (
    id bigserial primary key,
    corp_code varchar(8) not null unique,
    stock_code varchar(6) not null unique,
    corp_name varchar(200) not null,
    corp_name_eng varchar(200),
    market varchar(20) not null default 'KOSPI',
    sector varchar(100),
    industry varchar(100),
    fiscal_month smallint,
    listed_at date,
    delisted_at date,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_companies_market_active on companies (market, is_active);
create index idx_companies_name on companies (corp_name);

create table company_listings (
    id bigserial primary key,
    company_id bigint not null references companies (id) on delete cascade,
    stock_code varchar(6) not null,
    stock_name varchar(200) not null,
    market varchar(20) not null,
    listed_at date,
    ended_at date,
    listing_status varchar(30) not null,
    source varchar(50) not null,
    unique (company_id, stock_code, market, listed_at)
);

create table dart_filings (
    id bigserial primary key,
    company_id bigint not null references companies (id) on delete cascade,
    rcept_no varchar(20) not null unique,
    report_code varchar(10) not null,
    report_name varchar(300) not null,
    report_year smallint not null,
    report_period varchar(10) not null,
    receipt_date date not null,
    filing_date date,
    is_consolidated boolean,
    source_url text,
    raw_payload jsonb,
    created_at timestamptz not null default now()
);

create index idx_dart_filings_company_period
    on dart_filings (company_id, report_year, report_period);
create index idx_dart_filings_receipt_date on dart_filings (receipt_date);

create table financial_statements (
    id bigserial primary key,
    company_id bigint not null references companies (id) on delete cascade,
    filing_id bigint references dart_filings (id) on delete set null,
    report_year smallint not null,
    report_period varchar(10) not null,
    statement_type varchar(20) not null,
    currency varchar(10) not null default 'KRW',
    unit bigint not null default 1,
    is_consolidated boolean not null default true,
    accounting_standard varchar(20),
    period_start date,
    period_end date not null,
    created_at timestamptz not null default now(),
    unique (
        company_id,
        report_year,
        report_period,
        statement_type,
        is_consolidated
    )
);

create table standard_accounts (
    id bigserial primary key,
    code varchar(80) not null unique,
    name_ko varchar(200) not null,
    statement_type varchar(20) not null,
    normal_sign smallint not null default 1,
    description text
);

create table financial_statement_items (
    id bigserial primary key,
    statement_id bigint not null references financial_statements (id) on delete cascade,
    account_id bigint references standard_accounts (id) on delete set null,
    dart_account_id varchar(100),
    account_name varchar(300) not null,
    account_detail varchar(300),
    amount numeric(24, 4),
    amount_previous numeric(24, 4),
    amount_before_previous numeric(24, 4),
    ordinal integer,
    raw_payload jsonb
);

create index idx_fsi_statement_account
    on financial_statement_items (statement_id, account_id);
create index idx_fsi_dart_account on financial_statement_items (dart_account_id);

create table account_aliases (
    id bigserial primary key,
    account_id bigint not null references standard_accounts (id) on delete cascade,
    source varchar(50) not null,
    dart_account_id varchar(100),
    raw_account_name varchar(300) not null,
    match_rule varchar(30) not null default 'EXACT',
    priority integer not null default 100,
    is_active boolean not null default true
);

create index idx_account_aliases_lookup
    on account_aliases (source, raw_account_name, is_active);
create index idx_account_aliases_dart_id on account_aliases (dart_account_id);

create table daily_prices (
    id bigserial primary key,
    company_id bigint not null references companies (id) on delete cascade,
    trade_date date not null,
    open numeric(18, 4),
    high numeric(18, 4),
    low numeric(18, 4),
    close numeric(18, 4) not null,
    adjusted_close numeric(18, 4),
    volume bigint,
    change_rate numeric(12, 8),
    market_cap numeric(24, 4),
    shares_outstanding numeric(24, 4),
    source varchar(50) not null,
    unique (company_id, trade_date)
);

create index idx_daily_prices_date on daily_prices (trade_date);

create table corporate_events (
    id bigserial primary key,
    company_id bigint not null references companies (id) on delete cascade,
    event_type varchar(50) not null,
    event_subtype varchar(100),
    event_date date not null,
    start_date date,
    end_date date,
    severity smallint,
    title varchar(300) not null,
    description text,
    source varchar(50) not null,
    source_id varchar(100),
    source_url text,
    raw_payload jsonb,
    created_at timestamptz not null default now()
);

create index idx_corporate_events_company_date
    on corporate_events (company_id, event_date);
create index idx_corporate_events_type_date
    on corporate_events (event_type, event_date);
create unique index uq_corporate_events_source_id
    on corporate_events (source, source_id)
    where source_id is not null;
create unique index uq_corporate_events_fallback
    on corporate_events (company_id, event_type, coalesce(event_subtype, ''), event_date, source)
    where source_id is null;

create table metric_definitions (
    id bigserial primary key,
    code varchar(80) not null unique,
    name varchar(200) not null,
    category varchar(50) not null,
    higher_is_better boolean,
    formula_version varchar(30) not null,
    description text,
    is_active boolean not null default true
);

create table metric_snapshots (
    id bigserial primary key,
    company_id bigint not null references companies (id) on delete cascade,
    as_of_date date not null,
    report_year smallint,
    report_period varchar(10),
    price_window_days integer,
    statement_basis varchar(20) not null,
    data_quality_score numeric(8, 4),
    calculation_status varchar(30) not null,
    error_message text,
    created_at timestamptz not null default now(),
    unique (
        company_id,
        as_of_date,
        report_year,
        report_period,
        statement_basis,
        price_window_days
    )
);

create index idx_metric_snapshots_asof on metric_snapshots (as_of_date);

create table metric_values (
    id bigserial primary key,
    snapshot_id bigint not null references metric_snapshots (id) on delete cascade,
    metric_id bigint not null references metric_definitions (id) on delete cascade,
    value numeric(24, 8),
    raw_components jsonb,
    interpretation varchar(50),
    confidence numeric(8, 4),
    note text,
    unique (snapshot_id, metric_id)
);

create table risk_assessments (
    id bigserial primary key,
    company_id bigint not null references companies (id) on delete cascade,
    snapshot_id bigint not null references metric_snapshots (id) on delete cascade,
    model_version varchar(30) not null,
    credit_grade varchar(20),
    risk_score numeric(8, 4) not null,
    risk_level varchar(30) not null,
    summary text,
    strengths jsonb,
    weaknesses jsonb,
    created_at timestamptz not null default now(),
    unique (snapshot_id, model_version)
);

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
    finished_at timestamptz,
    check (
        status in (
            'QUEUED',
            'RUNNING',
            'SUCCESS',
            'PARTIAL_SUCCESS',
            'FAILED',
            'CANCELED'
        )
    )
);

create index idx_data_collection_jobs_status_created
    on data_collection_jobs (status, created_at);
create index idx_data_collection_jobs_type_created
    on data_collection_jobs (job_type, created_at);
create index idx_data_collection_jobs_parent
    on data_collection_jobs (parent_job_id);

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
    updated_at timestamptz not null default now(),
    check (
        recommended_interval in (
            'DAILY',
            'WEEKLY',
            'MONTHLY',
            'QUARTERLY'
        )
    )
);

create index idx_collection_schedules_active_next
    on collection_schedules (is_active, next_recommended_at);

insert into collection_schedules (
    schedule_code,
    job_type,
    market,
    recommended_interval,
    params
) values
    (
        'kospi_companies_monthly',
        'COLLECT_COMPANIES',
        'KOSPI',
        'MONTHLY',
        '{"source": "FDR"}'::jsonb
    ),
    (
        'kospi_filings_quarterly',
        'COLLECT_FILINGS',
        'KOSPI',
        'QUARTERLY',
        '{"report_codes": ["11011", "11013", "11012", "11014"]}'::jsonb
    ),
    (
        'kospi_financials_quarterly',
        'COLLECT_FINANCIALS',
        'KOSPI',
        'QUARTERLY',
        '{"basis": "CONSOLIDATED"}'::jsonb
    ),
    (
        'kospi_prices_daily',
        'COLLECT_PRICES',
        'KOSPI',
        'DAILY',
        '{}'::jsonb
    ),
    (
        'kospi_events_daily',
        'COLLECT_EVENTS',
        'KOSPI',
        'DAILY',
        '{"event_types": ["MANAGEMENT_ISSUE", "AUDIT_OPINION", "TRADING_SUSPENSION"]}'::jsonb
    );
