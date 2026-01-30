-- MySQL Database Schema for Auth and Tenants (Sub-schema)
-- 用于存储租户、用户及权限管理的表结构
-- 
-- ⚠️ 注意：本文件是认证/租户表子集。
-- 建议直接执行 schema.sql 以获得完整的数据库结构。

-- 1. 租户表（tenants）
CREATE TABLE tenants (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '租户ID',
    tenant_key VARCHAR(255) NOT NULL UNIQUE COMMENT '租户唯一字符串标识，用于路由/API/隔离',
    tenant_name VARCHAR(255) NOT NULL UNIQUE COMMENT '租户显示名称',
    subdomain VARCHAR(100) UNIQUE COMMENT '租户子域名',
    company_legal_name VARCHAR(255) COMMENT '企业法定名称',
    company_type VARCHAR(100) COMMENT '企业类型',
    registration_no VARCHAR(100) COMMENT '企业注册号/统一社会信用代码',
    industry VARCHAR(100) COMMENT '行业',
    contact_name VARCHAR(100) COMMENT '联系人姓名',
    contact_email VARCHAR(255) COMMENT '联系人邮箱',
    contact_phone VARCHAR(50) COMMENT '联系人电话',
    status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '租户状态',
    plan_type VARCHAR(50) COMMENT '订阅计划类型',
    max_users INT DEFAULT 10 COMMENT '最大用户数',
    billing_cycle VARCHAR(50) COMMENT '计费周期（monthly/yearly）',
    contract_start_date DATE COMMENT '合同开始日期',
    contract_end_date DATE COMMENT '合同结束日期',
    created_by VARCHAR(36) COMMENT '创建人user_key（平台操作员）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_tenant_key (tenant_key),
    INDEX idx_subdomain (subdomain)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 用户表（users）
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    user_key VARCHAR(36) NOT NULL UNIQUE COMMENT '用户全局唯一字符串ID（如 UUID/ULID）',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '登录邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    first_name VARCHAR(100) COMMENT '名',
    last_name VARCHAR(100) COMMENT '姓',
    phone_number VARCHAR(50) COMMENT '手机号',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已验证',
    status ENUM('pending_activation', 'active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '用户状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 用户-租户关系表（核心多租户关联）
-- 采用此表支持一个用户属于多个租户（如：开发者在 A 租户是管理员，在 B 租户是成员）
CREATE TABLE user_tenants (
    user_id BIGINT NOT NULL COMMENT '关联 users.id',
    tenant_id BIGINT NOT NULL COMMENT '关联 tenants.id',
    role VARCHAR(50) NOT NULL DEFAULT 'member' COMMENT '租户内角色：admin, member, viewer 等',
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active' COMMENT '在该租户下的状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    PRIMARY KEY (user_id, tenant_id),
    INDEX idx_tenant_user (tenant_id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 租户配置表（tenant_configs）
CREATE TABLE tenant_configs (
    tenant_id BIGINT PRIMARY KEY COMMENT '关联 tenants.id',
    theme_color VARCHAR(20) DEFAULT '#3498db' COMMENT '主题色',
    logo_url VARCHAR(512) COMMENT 'Logo 地址',
    custom_domain VARCHAR(255) COMMENT '自定义域名，如 app.acmecorp.com',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invitation_codes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '邀请码ID',
    tenant_id BIGINT NOT NULL COMMENT '所属租户ID',
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '邀请码（6位）',
    
    status ENUM('active', 'inactive', 'expired') NOT NULL DEFAULT 'active' COMMENT '邀请码状态',
    max_uses INT NULL COMMENT '最大使用次数（NULL=无限制）',
    usage_count INT DEFAULT 0 COMMENT '已使用次数',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    
    created_by BIGINT COMMENT '创建人user_id',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_code (code),
    INDEX idx_status (status),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
