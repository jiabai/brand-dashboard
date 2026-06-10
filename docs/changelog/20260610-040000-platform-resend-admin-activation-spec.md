# 平台重发管理员激活邮件规格

## 变更

- 新增产品规格 `docs/product-specs/20260610-platform-resend-admin-activation.md`：定义平台租户详情页对「待激活」管理员重发激活邮件的流程、API 行为、页面行为、安全要求和验收标准。
- 更新 `docs/product-specs/index.md` 索引。

## 边界

- 本次提交仅包含规格文档，不含实现。
- 范围限定为平台侧重发入口；不含自助重发、邮箱修改、列表筛选与超期警示。

## 验证

- `python scripts/validate_agents_docs.py --level ERROR`
