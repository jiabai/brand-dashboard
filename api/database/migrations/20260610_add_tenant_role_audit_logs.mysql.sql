CREATE TABLE IF NOT EXISTS tenant_role_audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '租户角色变更审计ID',
    tenant_id BIGINT NOT NULL COMMENT '关联 tenants.id',
    target_user_id BIGINT NOT NULL COMMENT '被修改的 users.id',
    actor_user_id BIGINT NOT NULL COMMENT '操作者 users.id',
    actor_scope ENUM('tenant', 'platform') NOT NULL COMMENT '操作范围',
    action ENUM('role_updated', 'status_updated', 'membership_updated') NOT NULL COMMENT '变更类型',
    old_role VARCHAR(50) COMMENT '变更前角色',
    new_role VARCHAR(50) COMMENT '变更后角色',
    old_status VARCHAR(20) COMMENT '变更前成员状态',
    new_status VARCHAR(20) COMMENT '变更后成员状态',
    reason TEXT COMMENT '变更原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_tenant_role_audit_tenant (tenant_id, created_at),
    INDEX idx_tenant_role_audit_target (target_user_id, created_at),
    INDEX idx_tenant_role_audit_actor (actor_user_id, created_at),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

