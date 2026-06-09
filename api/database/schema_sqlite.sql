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


-- Monitoring project configuration model
CREATE TABLE IF NOT EXISTS monitoring_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    category VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'archived')),
    created_by INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, project_id),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_monitoring_projects_tenant_status ON monitoring_projects (tenant_key, status);
CREATE INDEX IF NOT EXISTS idx_monitoring_projects_tenant_category ON monitoring_projects (tenant_key, category);

CREATE TRIGGER trg_monitoring_projects_updated_at
AFTER UPDATE ON monitoring_projects
FOR EACH ROW
BEGIN
    UPDATE monitoring_projects SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS project_brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    brand_id VARCHAR(128) NOT NULL,
    brand_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'competitor' CHECK (role IN ('target', 'competitor', 'watch_only')),
    aliases TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, project_id, brand_id, role),
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_project_brands_project_role ON project_brands (tenant_key, project_id, role);
CREATE INDEX IF NOT EXISTS idx_project_brands_brand ON project_brands (tenant_key, brand_id);

CREATE TRIGGER trg_project_brands_updated_at
AFTER UPDATE ON project_brands
FOR EACH ROW
BEGIN
    UPDATE project_brands SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS prompt_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    prompt_set_id VARCHAR(128) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    name VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, prompt_set_id),
    UNIQUE (tenant_key, project_id, version),
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_prompt_sets_project_status ON prompt_sets (tenant_key, project_id, status);

CREATE TRIGGER trg_prompt_sets_updated_at
AFTER UPDATE ON prompt_sets
FOR EACH ROW
BEGIN
    UPDATE prompt_sets SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS prompt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    prompt_set_id VARCHAR(128) NOT NULL,
    prompt_item_id VARCHAR(128) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    query_content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, prompt_set_id, prompt_item_id),
    FOREIGN KEY (tenant_key, prompt_set_id) REFERENCES prompt_sets(tenant_key, prompt_set_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_prompt_items_prompt_set_status ON prompt_items (tenant_key, prompt_set_id, status);
CREATE INDEX IF NOT EXISTS idx_prompt_items_keyword ON prompt_items (tenant_key, keyword);

CREATE TRIGGER trg_prompt_items_updated_at
AFTER UPDATE ON prompt_items
FOR EACH ROW
BEGIN
    UPDATE prompt_items SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
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

-- 9. Collection lifecycle model
CREATE TABLE IF NOT EXISTS collection_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    collection_job_id VARCHAR(128) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    prompt_set_id VARCHAR(128),
    source_job_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'expired', 'cancelled')),
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    expected_task_count INTEGER NOT NULL DEFAULT 0,
    succeeded_task_count INTEGER NOT NULL DEFAULT 0,
    failed_task_count INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, collection_job_id),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id),
    FOREIGN KEY (tenant_key, prompt_set_id) REFERENCES prompt_sets(tenant_key, prompt_set_id)
);
CREATE INDEX IF NOT EXISTS idx_collection_jobs_tenant_project_status ON collection_jobs (tenant_key, project_id, status);
CREATE INDEX IF NOT EXISTS idx_collection_jobs_prompt_set ON collection_jobs (tenant_key, prompt_set_id);
CREATE INDEX IF NOT EXISTS idx_collection_jobs_source_job ON collection_jobs (tenant_key, source_job_id);

CREATE TRIGGER trg_collection_jobs_updated_at
AFTER UPDATE ON collection_jobs
FOR EACH ROW
BEGIN
    UPDATE collection_jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS collection_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    collection_task_id VARCHAR(128) NOT NULL,
    collection_job_id VARCHAR(128) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    prompt_set_id VARCHAR(128),
    prompt_item_id VARCHAR(128),
    platform VARCHAR(64) NOT NULL,
    query_content TEXT NOT NULL,
    run_index INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reserved', 'running', 'succeeded', 'failed', 'expired', 'cancelled')),
    lease_owner VARCHAR(128),
    lease_until TIMESTAMP,
    reserved_at TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    last_error_code VARCHAR(64),
    last_error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, collection_task_id),
    FOREIGN KEY (tenant_key, collection_job_id) REFERENCES collection_jobs(tenant_key, collection_job_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id),
    FOREIGN KEY (tenant_key, prompt_set_id, prompt_item_id) REFERENCES prompt_items(tenant_key, prompt_set_id, prompt_item_id),
    FOREIGN KEY (lease_owner) REFERENCES executors(executor_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_collection_tasks_fetch ON collection_tasks (tenant_key, status, lease_until, id);
CREATE INDEX IF NOT EXISTS idx_collection_tasks_job_status ON collection_tasks (tenant_key, collection_job_id, status);
CREATE INDEX IF NOT EXISTS idx_collection_tasks_project ON collection_tasks (tenant_key, project_id, status);
CREATE INDEX IF NOT EXISTS idx_collection_tasks_prompt ON collection_tasks (tenant_key, prompt_set_id, prompt_item_id);
CREATE INDEX IF NOT EXISTS idx_collection_tasks_lease_owner ON collection_tasks (lease_owner, status, tenant_key);

CREATE TRIGGER trg_collection_tasks_updated_at
AFTER UPDATE ON collection_tasks
FOR EACH ROW
BEGIN
    UPDATE collection_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS collection_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    attempt_id VARCHAR(128) NOT NULL,
    collection_task_id VARCHAR(128) NOT NULL,
    executor_id VARCHAR(128),
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'succeeded', 'failed', 'timeout', 'cancelled')),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    error_code VARCHAR(64),
    error_message TEXT,
    raw_response_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, attempt_id),
    FOREIGN KEY (tenant_key, collection_task_id) REFERENCES collection_tasks(tenant_key, collection_task_id) ON DELETE CASCADE,
    FOREIGN KEY (executor_id) REFERENCES executors(executor_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_collection_attempts_task ON collection_attempts (tenant_key, collection_task_id);
CREATE INDEX IF NOT EXISTS idx_collection_attempts_executor_status ON collection_attempts (tenant_key, executor_id, status);
CREATE INDEX IF NOT EXISTS idx_collection_attempts_executor_fk ON collection_attempts (executor_id);

CREATE TRIGGER trg_collection_attempts_updated_at
AFTER UPDATE ON collection_attempts
FOR EACH ROW
BEGIN
    UPDATE collection_attempts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 10. Analysis run lifecycle model
CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    analysis_run_id VARCHAR(128) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    collection_job_id VARCHAR(128) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'succeeded', 'failed', 'stale')),
    plugin_versions TEXT,
    model_config_hash VARCHAR(128),
    input_watermark VARCHAR(255),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    stale_at TIMESTAMP,
    error_code VARCHAR(64),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, analysis_run_id),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id),
    FOREIGN KEY (tenant_key, collection_job_id) REFERENCES collection_jobs(tenant_key, collection_job_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_tenant_project_status ON analysis_runs (tenant_key, project_id, status);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_collection_job ON analysis_runs (tenant_key, collection_job_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_status_updated ON analysis_runs (tenant_key, status, updated_at);

CREATE TRIGGER trg_analysis_runs_updated_at
AFTER UPDATE ON analysis_runs
FOR EACH ROW
BEGIN
    UPDATE analysis_runs SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 11. Alert rule and event read model
CREATE TABLE IF NOT EXISTS alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    alert_rule_id VARCHAR(128) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(32) NOT NULL CHECK (rule_type IN ('metric_drop', 'metric_rise', 'metric_change')),
    metric_name VARCHAR(64) NOT NULL,
    metric_definition_version VARCHAR(32) NOT NULL DEFAULT 'brand_metrics_v1',
    brand_id VARCHAR(128) NOT NULL DEFAULT '',
    brand_name VARCHAR(255),
    platform VARCHAR(64) NOT NULL DEFAULT '',
    keyword VARCHAR(100) NOT NULL DEFAULT '',
    threshold_value DECIMAL(18,6) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'critical')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, alert_rule_id),
    UNIQUE (
        tenant_key,
        project_id,
        rule_type,
        metric_name,
        metric_definition_version,
        brand_id,
        platform,
        keyword
    ),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id)
);
CREATE INDEX IF NOT EXISTS idx_alert_rules_project_status ON alert_rules (tenant_key, project_id, status);
CREATE INDEX IF NOT EXISTS idx_alert_rules_metric ON alert_rules (tenant_key, project_id, metric_name, rule_type);

CREATE TRIGGER trg_alert_rules_updated_at
AFTER UPDATE ON alert_rules
FOR EACH ROW
BEGIN
    UPDATE alert_rules SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    alert_event_id VARCHAR(128) NOT NULL,
    alert_rule_id VARCHAR(128) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    analysis_run_id VARCHAR(128) NOT NULL,
    collection_job_id VARCHAR(128) NOT NULL,
    metric_date DATE NOT NULL,
    metric_name VARCHAR(64) NOT NULL,
    metric_definition_version VARCHAR(32) NOT NULL DEFAULT 'brand_metrics_v1',
    brand_id VARCHAR(128) NOT NULL DEFAULT '',
    brand_name VARCHAR(255),
    platform VARCHAR(64) NOT NULL DEFAULT '',
    keyword VARCHAR(100) NOT NULL DEFAULT '',
    dimension_hash VARCHAR(64) NOT NULL,
    previous_metric_date DATE,
    previous_value DECIMAL(18,6),
    current_value DECIMAL(18,6) NOT NULL,
    delta_value DECIMAL(18,6) NOT NULL,
    threshold_value DECIMAL(18,6) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'critical')),
    event_status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (event_status IN ('open', 'acknowledged', 'resolved')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, alert_event_id),
    UNIQUE (tenant_key, alert_rule_id, analysis_run_id, metric_date, dimension_hash),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id),
    FOREIGN KEY (tenant_key, alert_rule_id) REFERENCES alert_rules(tenant_key, alert_rule_id),
    FOREIGN KEY (tenant_key, analysis_run_id) REFERENCES analysis_runs(tenant_key, analysis_run_id)
);
CREATE INDEX IF NOT EXISTS idx_alert_events_project_status ON alert_events (tenant_key, project_id, event_status, triggered_at);
CREATE INDEX IF NOT EXISTS idx_alert_events_analysis_run ON alert_events (tenant_key, analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_alert_events_rule ON alert_events (tenant_key, alert_rule_id);

CREATE TRIGGER trg_alert_events_updated_at
AFTER UPDATE ON alert_events
FOR EACH ROW
BEGIN
    UPDATE alert_events SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- 11. 用户监测任务记录表
CREATE TABLE IF NOT EXISTS generated_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    report_id VARCHAR(128) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    report_type VARCHAR(32) NOT NULL DEFAULT 'project_summary'
        CHECK (report_type IN ('project_summary')),
    title VARCHAR(255) NOT NULL,
    timeframe VARCHAR(32) NOT NULL DEFAULT 'custom'
        CHECK (timeframe IN ('custom', 'daily', 'weekly', 'monthly')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'generated'
        CHECK (status IN ('generated', 'failed')),
    summary_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    alerts_json TEXT,
    generated_by INTEGER,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_key, report_id),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, project_id) REFERENCES monitoring_projects(tenant_key, project_id)
);
CREATE INDEX IF NOT EXISTS idx_generated_reports_project_generated ON generated_reports (tenant_key, project_id, generated_at);
CREATE INDEX IF NOT EXISTS idx_generated_reports_project_window ON generated_reports (tenant_key, project_id, start_date, end_date);

CREATE TRIGGER trg_generated_reports_updated_at
AFTER UPDATE ON generated_reports
FOR EACH ROW
BEGIN
    UPDATE generated_reports SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS llm_query_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_key VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    project_id VARCHAR(128),
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
CREATE INDEX IF NOT EXISTS idx_lqj_project ON llm_query_jobs (tenant_key, project_id);
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
    analysis_run_id VARCHAR(128),
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
    CONSTRAINT uk_tenant_job_conv_brand UNIQUE (tenant_key, job_id, conversation_id, brand),
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, analysis_run_id) REFERENCES analysis_runs(tenant_key, analysis_run_id)
);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_date ON qa_brand_state (tenant_key, date);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_brand ON qa_brand_state (tenant_key, brand);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_platform ON qa_brand_state (tenant_key, platform);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_sentiment ON qa_brand_state (tenant_key, sentiment_status);
CREATE INDEX IF NOT EXISTS idx_qbrs_tenant_conversation ON qa_brand_state (tenant_key, conversation_id);
CREATE INDEX IF NOT EXISTS idx_qbrs_analysis_run ON qa_brand_state (tenant_key, analysis_run_id);

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
    analysis_run_id VARCHAR(128),
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
    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE,
    FOREIGN KEY (tenant_key, analysis_run_id) REFERENCES analysis_runs(tenant_key, analysis_run_id)
);
CREATE INDEX IF NOT EXISTS idx_qr_platform ON qa_reference (platform);
CREATE INDEX IF NOT EXISTS idx_qr_brand ON qa_reference (brand);
CREATE INDEX IF NOT EXISTS idx_qr_category ON qa_reference (category);
CREATE INDEX IF NOT EXISTS idx_qr_keyword ON qa_reference (keyword);
CREATE INDEX IF NOT EXISTS idx_qr_domain ON qa_reference (domain);
CREATE INDEX IF NOT EXISTS idx_qr_content_type ON qa_reference (content_type);
CREATE INDEX IF NOT EXISTS idx_qr_is_published_link ON qa_reference (is_published_link);
CREATE INDEX IF NOT EXISTS idx_qr_analysis_run ON qa_reference (tenant_key, analysis_run_id);

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
