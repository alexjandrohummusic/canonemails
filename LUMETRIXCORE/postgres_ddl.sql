-- Canon Backend PostgreSQL DDL
-- Run with: psql "$DATABASE_URL" -f migrations/postgres_ddl.sql

CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    visible_name VARCHAR(160) NOT NULL,
    retention_days INTEGER NOT NULL DEFAULT 15,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(160) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users (tenant_id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS api_tokens (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    provider VARCHAR(40) NOT NULL,
    encrypted_token TEXT NOT NULL,
    last_verified_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_token_provider_per_tenant UNIQUE (tenant_id, provider)
);

CREATE INDEX IF NOT EXISTS ix_api_tokens_tenant_id ON api_tokens (tenant_id);

CREATE TABLE IF NOT EXISTS sender_profiles (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    from_name VARCHAR(160) NOT NULL,
    from_email VARCHAR(255) NOT NULL,
    reply_to VARCHAR(255) NULL,
    domain VARCHAR(255) NOT NULL,
    dkim_verified BOOLEAN NOT NULL DEFAULT FALSE,
    spf_verified BOOLEAN NOT NULL DEFAULT FALSE,
    dmarc_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_sender_profiles_tenant_id ON sender_profiles (tenant_id);

CREATE TABLE IF NOT EXISTS send_profiles (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    timezone VARCHAR(80) NOT NULL DEFAULT 'America/Mexico_City',
    hourly_limit INTEGER NOT NULL DEFAULT 300,
    daily_limit INTEGER NOT NULL DEFAULT 1500,
    quiet_hours JSON NOT NULL DEFAULT '{}'::json,
    warmup_curve JSON NOT NULL DEFAULT '{}'::json,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_send_profiles_tenant_id ON send_profiles (tenant_id);

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(120) NOT NULL,
    subcategory VARCHAR(120) NULL,
    landing_url VARCHAR(600) NULL,
    checkout_url VARCHAR(600) NULL,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    is_order_bump BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT NULL,
    metadata_json JSON NOT NULL DEFAULT '{}'::json,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_products_tenant_id ON products (tenant_id);

CREATE TABLE IF NOT EXISTS campaigns (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    name VARCHAR(180) NOT NULL,
    requested_mode VARCHAR(40) NOT NULL DEFAULT 'auto',
    status VARCHAR(40) NOT NULL DEFAULT 'draft',
    source_filename VARCHAR(300) NULL,
    output_txt_path VARCHAR(600) NULL,
    output_xlsx_path VARCHAR(600) NULL,
    send_cursor INTEGER NOT NULL DEFAULT 0,
    metrics JSON NOT NULL DEFAULT '{}'::json,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_campaigns_tenant_id ON campaigns (tenant_id);

CREATE TABLE IF NOT EXISTS campaign_recipients (
    id VARCHAR(36) PRIMARY KEY,
    campaign_id VARCHAR(36) NOT NULL REFERENCES campaigns(id),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(180) NOT NULL,
    product_name VARCHAR(255) NULL,
    subject VARCHAR(255) NULL,
    mode VARCHAR(40) NOT NULL DEFAULT 'auto',
    audience VARCHAR(120) NULL,
    interest VARCHAR(120) NULL,
    delivery_status VARCHAR(40) NOT NULL DEFAULT 'pending',
    provider_message_id VARCHAR(255) NULL,
    payload JSON NOT NULL DEFAULT '{}'::json,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_campaign_recipients_campaign_id
    ON campaign_recipients (campaign_id);
CREATE INDEX IF NOT EXISTS ix_campaign_recipients_email
    ON campaign_recipients (email);

CREATE TABLE IF NOT EXISTS suppression_entries (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL,
    reason VARCHAR(80) NOT NULL,
    source VARCHAR(80) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_suppression_email_per_tenant UNIQUE (tenant_id, email)
);

CREATE INDEX IF NOT EXISTS ix_suppression_entries_tenant_id
    ON suppression_entries (tenant_id);
CREATE INDEX IF NOT EXISTS ix_suppression_entries_email
    ON suppression_entries (email);

-- 1. TENANTS
INSERT INTO tenants (id, name, visible_name, retention_days) VALUES
('t0000001-0000-0000-0000-000000000000', 'tech_corp', 'Tech Corporation', 30),
('t0000002-0000-0000-0000-000000000000', 'marketing_pro', 'Marketing Pro Agency', 60),
('t0000003-0000-0000-0000-000000000000', 'eco_store', 'Eco Friendly Store', 15),
('t0000004-0000-0000-0000-000000000000', 'edu_latam', 'Educación Latam', 90),
('t0000005-0000-0000-0000-000000000000', 'fitness_app', 'Fit & Health App', 30),
('t0000006-0000-0000-0000-000000000000', 'travel_guru', 'Travel Guru', 15),
('t0000007-0000-0000-0000-000000000000', 'finance_now', 'Finance Now', 120),
('t0000008-0000-0000-0000-000000000000', 'real_estate_mx', 'Inmobiliaria MX', 45),
('t0000009-0000-0000-0000-000000000000', 'gourmet_box', 'Gourmet Box', 15),
('t0000010-0000-0000-0000-000000000000', 'saas_startup', 'SaaS Innovators', 60);


INSERT INTO users (id, tenant_id, email, full_name, is_active) VALUES
('u0000001-0000-0000-0000-000000000000', 't0000001-0000-0000-0000-000000000000', 'admin@techcorp.com', 'Carlos Mendoza', true),
('u0000002-0000-0000-0000-000000000000', 't0000002-0000-0000-0000-000000000000', 'maria@marketingpro.com', 'Maria Gomez', true);