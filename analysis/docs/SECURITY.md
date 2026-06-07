# Security Baseline

## Purpose

本项目会接触数据库凭据、LLM API Key、用户问答文本、引用 URL 和运行结果，因此安全规范默认适用于配置、日志、插件、数据库和输出文件。

## Secrets

- 不在代码中硬编码 API Key、数据库密码或完整连接串。
- 本地 `.env` 只能作为开发机配置来源，不作为文档或测试样例事实来源。
- 示例配置应使用占位符；真实部署凭据通过环境变量、密钥管理器或私有配置注入。
- 日志和异常信息不得打印密钥、密码或带凭据的 URL。

## Database

- 表名和字段名必须校验后再用于 SQLAlchemy 查询。
- 用户输入只作为过滤值，不拼接到 SQL 字符串中。
- 写入 `qa_brand_state`、`qa_reference` 等业务表时保持幂等，避免重复运行污染统计。
- schema 变化必须同步 `database/`、产品规格和迁移/回滚说明。

## LLM And External APIs

- LLM 调用边界要保留 timeout、retry 和 provider 信息，避免无限等待。
- 不把原始敏感问答、客户数据或凭据写入 prompt、日志或公开输出。
- 真实 LLM smoke test 应在最终说明中标记网络和密钥依赖，不要求默认测试运行。

## Files And Outputs

- `output/` 是运行产物，不能作为长期规范或手动编辑来源。
- 导入插件读取目录时必须限制在明确配置的目录内，并记录失败文件。
- JSON 输出应使用 UTF-8，避免混入二进制或不可序列化对象。

## Current Watch Items

- `config/analysis_config.json` 已改为环境变量占位符；真实数据库凭据必须通过环境变量、未跟踪的 `.env` 或密钥管理器注入。
- `.env` 存在于工作区，确认 `.gitignore` 持续忽略它。
- `tests/*_test.py` 中涉及真实 provider 的测试应默认视为手动/集成验证，避免在无密钥环境中误跑。
