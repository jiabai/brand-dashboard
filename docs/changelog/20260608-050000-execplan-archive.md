# Phase 8.3 ExecPlan 归档

## 变更内容

- 将品牌监测业务系统重构 ExecPlan 从 `docs/exec-plans/active/` 移动到 `docs/exec-plans/completed/`。
- 更新 active/completed ExecPlan index，active index 现在显示当前无进行中的 ExecPlan。
- 删除根目录 `TASKS.md`，符合“任务清单只在进行中任务存在时保留”的项目规则。
- 同步技术债记录中的 ExecPlan 引用到 completed 路径，并补充归档后的 Outcomes & Retrospective。

## 验证

- `uv run --project api ruff check api` 通过。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（169 passed, 1572 warnings）。
- `npm --prefix web test` 通过（88 passed）。
- `npm --prefix web run lint` 通过，0 errors，保留既有 8 warnings。
- `npm --prefix web run build` 通过。
- `python scripts/validate_agents_docs.py --level ERROR` 通过，0 错误。
- `python scripts/validate_agents_docs.py --level WARN` 通过，0 警告。
- `git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。
