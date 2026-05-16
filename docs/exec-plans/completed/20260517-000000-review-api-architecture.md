# API 架构审查与低风险修复

## Summary

对 `api/` 目录做了一轮架构与 bug 审查，重点检查多租户过滤、路由/仓储分层、执行器任务上报和运行时依赖。已完成低风险修复，并记录仍需单独设计的安全债。

## Code Changes

1. 将 `executors`、`query_jobs`、`conversation` 路由中的 SQL 下沉到 `api/v1/repositories/`：
   - `executors.py`
   - `query_jobs.py`
   - `conversation.py`
   - `tenants.py`
2. 修复 `query_jobs/report` 上报更新时缺少 `executor_id` 过滤的问题，避免仅凭任务主键更新非本执行器任务。
3. 修复 `LLMOperator.get_config_info()` 访问不存在配置字段的问题。
4. 补充 `api/requirements.txt` 中直接导入或测试所需依赖。
5. 更新测试 patch 目标，使测试贴合当前 `DashboardService -> Repositories` 架构。

## Findings

- 业务路由仍未对登录 token 和租户成员关系做统一授权校验，已记录到 `docs/exec-plans/tech-debt-tracker.md`。
- `api/config/llm_settings.json` 已被 Git 跟踪，存在密钥治理风险，已记录到技术债。
- 数据库 engine 在 import 时创建，测试会产生 ResourceWarning，已记录到技术债。

## Verification

- [x] `ruff check api`
- [x] `python -m unittest discover api/tests`
- [x] `python scripts\validate_agents_docs.py --level ERROR`

## Residual Risk

本次没有一次性引入全局 `get_current_user` 和租户成员授权，因为这会改变 API 调用契约，需要单独 spec、前端联调和迁移计划。
