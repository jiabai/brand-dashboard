-- ==========================================================
-- Brand Dashboard SQLite Schema
-- 与 schema.sql 功能等价，适配 SQLite 语法
-- ==========================================================

-- ---------------------------------------------------------
-- PART 1: Tenants and Users (Auth & Infrastructure)
-- ---------------------------------------------------------

-- 1. 租户表（tenants）
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL UNIQUE,
    tenant_name VARCHAR(255) NOT NULL UNIQUE,
    subdomain VARCHAR(100) UNIQUE,
    company_legal_name VARCHAR(255),
    company_type VARCHAR(100),
    registration_no VARCHAR(100),
    industry VARCHAR(100),
    contact_name VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    plan_type VARCHAR(50),
    max_users INTEGER DEFAULT 10,
    billing_cycle VARCHAR(50),
    contract_start_date DATE,
    contract_end_date DATE,
    created_by VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tenant_key ON tenants (tenant_key);
CREATE INDEX IF NOT EXISTS idx_subdomain ON tenants (subdomain);

-- updated_at 自动更新触发器
CREATE TRIGGER trg_tenants_updated_at
AFTER UPDATE ON tenants
FOR EACH ROW
BEGIN
    UPDATE tenants SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 2. 用户表（users）
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_key VARCHAR(36) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(50),
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('pending_activation', 'active', 'inactive', 'suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 3. 用户-租户关系表（核心多租户关联）
CREATE TABLE IF NOT EXISTS user_tenants (
    user_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, tenant_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tenant_user ON user_tenants (tenant_id, user_id);

-- 4. 租户配置表（tenant_configs）
CREATE TABLE IF NOT EXISTS tenant_configs (
    tenant_id INTEGER PRIMARY KEY,
    theme_color VARCHAR(20) DEFAULT '#3498db',
    logo_url VARCHAR(512),
    custom_domain VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TRIGGER trg_tenant_configs_updated_at
AFTER UPDATE ON tenant_configs
FOR EACH ROW
BEGIN
    UPDATE tenant_configs SET updated_at = CURRENT_TIMESTAMP WHERE tenant_id = OLD.tenant_id;
END;

-- 5. 邀请码表
CREATE TABLE IF NOT EXISTS invitation_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'expired')),
    max_uses INTEGER NULL,
    usage_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP NULL,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ic_tenant_id ON invitation_codes (tenant_id);
CREATE INDEX IF NOT EXISTS idx_ic_code ON invitation_codes (code);
CREATE INDEX IF NOT EXISTS idx_ic_status ON invitation_codes (status);

CREATE TRIGGER trg_invitation_codes_updated_at
AFTER UPDATE ON invitation_codes
FOR EACH ROW
BEGIN
    UPDATE invitation_codes SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;


-- ---------------------------------------------------------
-- PART 2: Business Logic (Conversations, Jobs, Analytics)
-- ---------------------------------------------------------

-- 6. LLM 对话内容主表
CREATE TABLE IF NOT EXISTS llm_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    platform VARCHAR(64) NOT NULL,
    brand VARCHAR(50),
    category VARCHAR(64) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    query_content TEXT NOT NULL,
    answer_content TEXT NOT NULL,
    generated_date DATE,
    extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, conversation_id),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_lc_tenant_job ON llm_conversations (tenant_key, job_id);
CREATE INDEX IF NOT EXISTS idx_lc_tenant_generated_date ON llm_conversations (tenant_key, generated_date);
CREATE INDEX IF NOT EXISTS idx_lc_platform ON llm_conversations (platform);
CREATE INDEX IF NOT EXISTS idx_lc_brand ON llm_conversations (brand);
CREATE INDEX IF NOT EXISTS idx_lc_category ON llm_conversations (category);
CREATE INDEX IF NOT EXISTS idx_lc_keyword ON llm_conversations (keyword);

CREATE TRIGGER trg_llm_conversations_updated_at
AFTER UPDATE ON llm_conversations
FOR EACH ROW
BEGIN
    UPDATE llm_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 7. 对话引用链接关联表
CREATE TABLE IF NOT EXISTS llm_conversation_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    platform VARCHAR(64) NOT NULL,
    brand VARCHAR(50),
    category VARCHAR(64) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    query_content TEXT NOT NULL,
    url VARCHAR(1024) NOT NULL,
    domain VARCHAR(100),
    cite_index INTEGER,
    site_name VARCHAR(255),
    content_type VARCHAR(50),
    generated_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, conversation_id, url),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, conversation_id) REFERENCES llm_conversations(tenant_key, conversation_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_lcr_tenant_job ON llm_conversation_references (tenant_key, job_id);
CREATE INDEX IF NOT EXISTS idx_lcr_tenant_generated_date ON llm_conversation_references (tenant_key, generated_date);
CREATE INDEX IF NOT EXISTS idx_lcr_platform ON llm_conversation_references (platform);
CREATE INDEX IF NOT EXISTS idx_lcr_brand ON llm_conversation_references (brand);
CREATE INDEX IF NOT EXISTS idx_lcr_category ON llm_conversation_references (category);
CREATE INDEX IF NOT EXISTS idx_lcr_keyword ON llm_conversation_references (keyword);
CREATE INDEX IF NOT EXISTS idx_lcr_domain ON llm_conversation_references (domain);
CREATE INDEX IF NOT EXISTS idx_lcr_content_type ON llm_conversation_references (content_type);

CREATE TRIGGER trg_llm_conversation_references_updated_at
AFTER UPDATE ON llm_conversation_references
FOR EACH ROW
BEGIN
    UPDATE llm_conversation_references SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 8. 执行器信息表
CREATE TABLE IF NOT EXISTS executors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    executor_id VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(64),
    status VARCHAR(20) DEFAULT 'active',
    ip_address VARCHAR(45) NOT NULL,
    api_key VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_executors_updated_at
AFTER UPDATE ON executors
FOR EACH ROW
BEGIN
    UPDATE executors SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 9. 用户监测任务记录表
CREATE TABLE IF NOT EXISTS llm_query_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL,
    brand VARCHAR(50),
    competitor TEXT,
    keyword VARCHAR(100) NOT NULL,
    query_content TEXT NOT NULL,
    query_status INTEGER NOT NULL DEFAULT 0 CHECK (query_status IN (0, 1, 2, 3)),
    executor_id VARCHAR(128),
    total_runs INTEGER NOT NULL DEFAULT 15,
    executed_runs INTEGER NOT NULL DEFAULT 0,
    last_executed_date DATE,
    effective_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (executor_id) REFERENCES executors(executor_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_lqj_tenant_job ON llm_query_jobs (tenant_key, job_id);
CREATE INDEX IF NOT EXISTS idx_lqj_brand ON llm_query_jobs (brand);
CREATE INDEX IF NOT EXISTS idx_lqj_category ON llm_query_jobs (category);
CREATE INDEX IF NOT EXISTS idx_lqj_keyword ON llm_query_jobs (keyword);
CREATE INDEX IF NOT EXISTS idx_lqj_created_at ON llm_query_jobs (created_at);
CREATE INDEX IF NOT EXISTS idx_lqj_executor_fetch ON llm_query_jobs (executor_id, query_status, is_deleted, executed_runs, id);
CREATE INDEX IF NOT EXISTS idx_lqj_daily_reset ON llm_query_jobs (query_status, is_deleted, last_executed_date, executed_runs);
CREATE INDEX IF NOT EXISTS idx_lqj_executor_fetch_date ON llm_query_jobs (executor_id, query_status, is_deleted, last_executed_date, id);

CREATE TRIGGER trg_llm_query_jobs_updated_at
AFTER UPDATE ON llm_query_jobs
FOR EACH ROW
BEGIN
    UPDATE llm_query_jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 10. 每日品牌情感和提及统计汇总表
CREATE TABLE IF NOT EXISTS qa_brand_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    brand VARCHAR(50) NOT NULL,
    product VARCHAR(255),
    platform VARCHAR(64) NOT NULL,
    question_count INTEGER NOT NULL,
    mention_count INTEGER NOT NULL,
    first_mention_count INTEGER NOT NULL,
    mention_rate DECIMAL(5,2) NOT NULL,
    first_mention_rate DECIMAL(5,2) NOT NULL,
    positive_count INTEGER NOT NULL,
    negative_count INTEGER NOT NULL,
    positive_ratio DECIMAL(5,2) NOT NULL,
    negative_ratio DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_qbs_tenant_date_brand ON qa_brand_summary (tenant_key, date, brand);
CREATE INDEX IF NOT EXISTS idx_qbs_tenant_platform ON qa_brand_summary (tenant_key, platform);
CREATE INDEX IF NOT EXISTS idx_qbs_tenant_brand_product ON qa_brand_summary (tenant_key, brand, product);

CREATE TRIGGER trg_qa_brand_summary_updated_at
AFTER UPDATE ON qa_brand_summary
FOR EACH ROW
BEGIN
    UPDATE qa_brand_summary SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 11. 品牌在问答中的具体状态记录表
CREATE TABLE IF NOT EXISTS qa_brand_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id VARCHAR(255) NOT NULL,
    tenant_key VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    brand VARCHAR(50) NOT NULL,
    category VARCHAR(64) NOT NULL,
    platform VARCHAR(64) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    is_mentioned INTEGER NOT NULL DEFAULT 0 CHECK (is_mentioned IN (0, 1)),
    is_first_mentioned INTEGER NOT NULL DEFAULT 0 CHECK (is_first_mentioned IN (0, 1)),
    is_top3_mentioned INTEGER NOT NULL DEFAULT 0 CHECK (is_top3_mentioned IN (0, 1)),
    sentiment_status VARCHAR(20) NOT NULL,
    brands_found TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_date ON qa_brand_state (tenant_key, date);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_brand ON qa_brand_state (tenant_key, brand);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_platform ON qa_brand_state (tenant_key, platform);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_sentiment ON qa_brand_state (tenant_key, sentiment_status);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_conversation ON qa_brand_state (tenant_key, conversation_id);

CREATE TRIGGER trg_qa_brand_state_updated_at
AFTER UPDATE ON qa_brand_state
FOR EACH ROW
BEGIN
    UPDATE qa_brand_state SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 12. 问答引用详情表
CREATE TABLE IF NOT EXISTS qa_reference (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id VARCHAR(255) NOT NULL,
    tenant_key VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    platform VARCHAR(64) NOT NULL,
    brand VARCHAR(50),
    category VARCHAR(64) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    query_content TEXT NOT NULL,
    url VARCHAR(1024) NOT NULL,
    is_published_link INTEGER NOT NULL DEFAULT 0 CHECK (is_published_link IN (0, 1)),
    domain VARCHAR(64),
    content_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, conversation_id, url),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_qr_platform ON qa_reference (platform);
CREATE INDEX IF NOT EXISTS idx_qr_brand ON qa_reference (brand);
CREATE INDEX IF NOT EXISTS idx_qr_category ON qa_reference (category);
CREATE INDEX IF NOT EXISTS idx_qr_keyword ON qa_reference (keyword);
CREATE INDEX IF NOT EXISTS idx_qr_domain ON qa_reference (domain);
CREATE INDEX IF NOT EXISTS idx_qr_content_type ON qa_reference (content_type);
CREATE INDEX IF NOT EXISTS idx_qr_is_published_link ON qa_reference (is_published_link);

CREATE TRIGGER trg_qa_reference_updated_at
AFTER UPDATE ON qa_reference
FOR EACH ROW
BEGIN
    UPDATE qa_reference SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- ==========================================================
-- SQLite Schema Creation Completed
-- 注意：MySQL 事件调度器（ev_reset_query_jobs_daily）需由应用层定时任务替代
-- 参见 api/v1/services/job_reset_scheduler.py
-- ==========================================================
