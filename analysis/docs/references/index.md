# References

## Purpose

本目录保存稳定的技术参考、插件说明和领域定义。它们解释“现有能力如何使用”，不记录执行进度；任务计划进入 `docs/exec-plans/`，用户可见范围进入 `docs/product-specs/`。

## Current References

| File | Scope |
|------|-------|
| `metrics-analysis.md` | 品牌分析指标定义和口径说明。 |
| `unified-llm-operator.md` | 统一 LLM 操作器的接口、provider 和使用参考。 |
| `plugins/llm-ping.md` | LLM Ping 工具插件的配置、运行方式和结果结构。 |

## Maintenance Rules

- 代码路径或配置结构变化时，同步更新对应参考文档。
- 参考文档可以包含示例，但示例不能使用真实密钥、密码或生产连接串。
- 若参考内容变成长期设计约束，将摘要同步到 `docs/DESIGN.md` 或 `docs/SECURITY.md`。
