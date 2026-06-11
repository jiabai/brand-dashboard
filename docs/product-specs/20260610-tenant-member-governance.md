# Tenant Member Governance

## 背景

当前系统已经区分平台管理员与租户内角色：`platform_admin` 来自平台级授权，`user_tenants.role` 表示某个租户内的 `admin/member/viewer`。这个边界是正确的，但现有实现还缺少租户成员管理 API、角色变更审计，以及最后一个租户管理员保护。

## 实施前满足情况

- 已满足：平台管理员创建租户时，可以指定首个 `adminEmail`，系统会写入 `user_tenants.role = 'admin'`。
- 未满足：租户管理员没有正式 HTTP API 管理本租户成员角色。
- 未满足：平台管理员没有受审计的应急/客服修改租户成员角色能力。
- 未满足：角色降级、停用或更新时没有保护“至少保留一个 active admin”。
- 未满足：CLI `grant_tenant_access.py` 可以直接更新角色，但没有写入审计日志，也没有最后管理员保护。

## 目标

1. 租户管理员可以通过受保护 API 查看本租户成员，并修改成员角色或状态。
2. 平台管理员可以通过平台 API 对指定租户执行应急/客服角色修改，但必须提交 `reason` 并写入审计日志。
3. 所有角色或成员状态变更都写入 `tenant_role_audit_logs`。
4. 任意租户在变更后必须至少保留一个 `active admin`。
5. 本地/部署 CLI 授权脚本继续可用，但角色更新与恢复必须复用同一保护规则并写入审计日志。

## 非目标

- 本次不实现前端成员管理页面。
- 本次不引入复杂审批流、双人复核或通知系统。
- 本次不把 `platform_admin` 从环境变量迁移到数据库；该问题单独规划。

## API 行为

### 租户管理员成员管理

- `GET /api/v1/tenants/{tenant_key}/members`
  - 权限：该租户 `admin`
  - 返回 active/inactive 成员列表，包含 user id、email、姓名、phone、role、status、createdAt。

- `PATCH /api/v1/tenants/{tenant_key}/members/{user_id}`
  - 权限：该租户 `admin`
  - 请求：`role`、`status` 至少传一个；可选 `reason`
  - 约束：不能把最后一个 active admin 降级或停用。

### 平台应急/客服修改

- `PATCH /api/v1/platform/tenants/{tenant_key}/members/{user_id}`
  - 权限：`platform_admin`
  - 请求：`role`、`status` 至少传一个；`reason` 必填。
  - 约束：不能把最后一个 active admin 降级或停用。
  - 审计：`actor_scope = 'platform'`，记录平台操作者与 reason。

## 审计日志

新增表 `tenant_role_audit_logs`：

- `id`
- `tenant_id`
- `target_user_id`
- `actor_user_id`
- `actor_scope`: `tenant` 或 `platform`
- `action`: `role_updated`、`status_updated`、`membership_updated`
- `old_role`、`new_role`
- `old_status`、`new_status`
- `reason`
- `created_at`

## 验收标准

- 租户管理员可以列出成员。
- 租户管理员可以把成员从 `member` 改为 `viewer`，并产生审计记录。
- 非 admin 租户成员不能调用成员管理 API。
- 平台管理员可以带 reason 修改租户成员角色，并产生平台范围审计记录。
- 平台管理员不带 reason 时请求失败。
- 最后一个 active admin 不能被降级或停用。
- `grant_tenant_access.py` 更新/恢复既有成员时写入审计，并拒绝降级最后一个 active admin。
- SQLite schema、MySQL schema 和迁移脚本同步。
