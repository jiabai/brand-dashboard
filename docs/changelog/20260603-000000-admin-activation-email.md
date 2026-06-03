# 管理员激活邮件发送

## 变更摘要

- 新增 SMTP 激活邮件发送流程：平台管理员创建租户成功后，系统会尝试向首个租户管理员邮箱发送激活链接。
- 创建租户响应新增 `emailDelivery`，用于标识 `sent`、`not_configured` 或 `failed`。
- 平台运营后台创建结果面板新增激活邮件状态提示，邮件未发送时保留人工复制激活链接的兜底路径。
- `/activate?token=...` 会自动读取 URL 中的 token 并填入激活表单。
- 新增产品规格和活动 ExecPlan，补充 API 参考文档。

## 安全说明

- SMTP 密码只从环境变量读取，不写入日志或错误响应。
- 邮件发送失败不回滚租户创建，也不向前端暴露 SMTP 异常细节。
- 租户列表接口仍不返回 activation token、activation URL 或 SMTP 配置。

## 验证

- `python -m pytest -p no:cacheprovider api/tests/test_email_sender.py api/tests/test_auth.py -q`
- `npm --prefix web run test -- src/components/platform/__tests__/tenantPresentation.test.js`
- `npm --prefix web run test -- src/auth/__tests__/activation.test.js`
