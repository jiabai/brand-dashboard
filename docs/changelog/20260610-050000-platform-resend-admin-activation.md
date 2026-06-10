# 平台重发租户管理员激活邮件

## 变更

- 新增 `POST /api/v1/platform/tenants/{tenant_key}/resend-activation`：平台管理员对「待激活」租户管理员重签 7 天激活令牌并重发激活邮件。
- 新增仓储函数 `regenerate_admin_activation`：按详情页同款规则（role='admin' 按 created_at 最早）定位管理员，校验 `pending_activation` 状态，只读不写库。
- 复用 `send_admin_activation_email`；SMTP 未配置/失败时接口仍返回 200，`emailDelivery` 区分状态，响应携带新激活链接供人工兜底。
- 前端新增 `resendPlatformTenantActivation` 适配器；租户详情页管理员卡片在待激活时显示「重发激活邮件」按钮，结果区展示邮件状态与可复制激活链接。
- 请求错误提示优先展示业务 `message` 字段（信封错误不再显示原始 JSON），并补齐 `detail` 回退路径测试。

## 边界

- 不支持修改管理员邮箱；不提供自助重发；不保存发送历史；不做频率限制。
- 不主动作废历史令牌；任一令牌激活成功后其余令牌全部失效。
- 仅平台管理员可触发；激活链接只出现在本次响应与邮件中。

## 验证

- `uv run --project api ruff check api`（All checks passed!）
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`（193 passed）
- `npm --prefix web test`（122 pass / 0 fail）
- `npm --prefix web run build`（构建成功）
- `python scripts/validate_agents_docs.py --level ERROR`（0 错误）
