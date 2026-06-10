# 自助密码重置与修改密码规格

## 变更

- 新增产品规格 `docs/product-specs/20260610-password-reset-and-change.md`：定义忘记密码邮件重置（防枚举、密码哈希指纹一次性令牌、60 秒冷却）与已登录修改密码的流程、API 行为、页面行为、安全要求和验收标准。
- 更新 `docs/product-specs/index.md` 索引（随分支批次提交）。

## 边界

- 本次提交仅包含规格文档，不含实现。
- 不含密码策略升级、JWT 会话失效、短信重置与平台侧代发重置邮件。

## 验证

- `python scripts/validate_agents_docs.py --level ERROR`
