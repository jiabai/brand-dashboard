# 项目详情页进入看板入口规格

## 变更

- 新增产品规格 `docs/product-specs/20260611-project-dashboard-entry.md`：定义租户用户从项目详情页选择某次采集 job 进入 legacy 首页看板的流程、API 行为（`GET /query-jobs/status` 增加可选 `project_id` 过滤）、页面行为（Sheet 选 job）、安全要求与验收标准。
- 更新 `docs/product-specs/index.md` 索引（随分支批次提交）。

## 边界

- 本次提交仅包含规格文档，不含实现。
- 仅项目详情页入口；不自动选最新 job；不改看板页与授权模型。

## 验证

- `python scripts/validate_agents_docs.py --level ERROR`
