# 自助密码重置与修改密码

## 变更

- 新增 `POST /api/v1/public/auth/forgot-password`：对 active 账号签发 1 小时重置令牌并发送重置邮件；防枚举（全路径统一响应、字节一致测试钉住）+ 按邮箱 60 秒进程级冷却（键小写规范化，规避 MySQL 大小写不敏感排序规则绕过）。
- 新增 `POST /api/v1/public/auth/reset-password`：校验令牌签名/类型/有效期/密码哈希指纹后原子条件更新密码；失败统一报「重置链接无效或已失效」。
- 新增 `POST /api/v1/auth/change-password`：已登录用户验证当前密码后修改密码。
- 一次性令牌语义：payload 携带 password_hash 的 SHA-256 指纹前 16 字符，密码变更后所有存量重置令牌自动失效；与激活令牌按 type 隔离。
- `email_sender` 新增 `send_password_reset_email`（复用 SMTP 基建，含 1 小时有效期与非本人操作提示）；发送非 sent 状态记服务端 warning（仅 status 与收件邮箱，不含令牌）。
- 登录页新增「重置」标签（申请邮件 + 凭令牌设新密码）与「忘记密码？」入口；`?token=` 自动填充改为路由感知，修复任意路由 token 参数被激活标签劫持的缺陷；新增 `/reset-password` 路由。
- 账户管理页新增「修改密码」表单（当前密码验证 + 两次一致性前置校验）。
- 前端新增 `forgotPassword`/`resetPassword`/`changePassword` API 适配器。
- `docs/SECURITY.md` 限流计划清单补充忘记密码与重置密码端点，并记录计时侧信道已知局限。

## 边界

- 不升级密码强度策略；不做密码历史/过期；不持久化重置令牌；不做短信重置。
- 重置/修改密码不失效已签发 JWT（无状态令牌已知局限，列为未来增强）。
- 平台侧代发重置邮件单独立项。

## 验证

- `uv run --project api ruff check api` → All checks passed
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` → 219 passed
- `npm --prefix web test` → 129 pass
- `npm --prefix web run build` → 构建成功
- `python scripts/validate_agents_docs.py --level ERROR` → 0 错误
