## Summary
- 在 README 中补充 Docker Compose 启动时 MySQL 容器的说明，包括数据库名称、root 密码与 API 端环境变量映射。

## Code Highlights
- `README.md`：在 Docker Compose 部分增加说明块，明确 `mysql` 服务（端口 3306）、默认数据库 `geo`、root 密码 `devpassword`，以及 `DB_HOST=mysql` 等环境变量配置。

## Self-Tests
- 手动检查 `README.md` 渲染片段，确认命令示例与当前 `docker-compose.yml` 中 `mysql` 服务配置一致。

