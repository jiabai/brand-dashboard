# API 非 Docker 部署指南

本文档说明如何在不使用 Docker 的情况下部署 `d:\Github\brand-dashboard\api\` 后端服务（FastAPI + MySQL）。

## 适用范围

- 运行方式：直接在宿主机（Linux/Windows/macOS）安装 Python 依赖并启动服务进程
- 数据库：MySQL 8.0+（utf8mb4）
- 默认端口：8000

## 目录与关键入口

- 应用入口：`api/main.py`（ASGI app：`api.main:app`）
- API 文档：
  - Swagger：`/api/v1/docs`
  - ReDoc：`/api/v1/redoc`
- 数据库脚本：`api/database/*.sql`
- LLM 配置：`api/config/llm_settings.json`
- 数据库连接配置：`api/.env`（可选，若存在会被加载）

## 环境要求

- Python：建议 3.11+（与 Ruff 配置一致）
- MySQL：8.0+，字符集 `utf8mb4`
- uv：Python 包管理器（推荐）

## 部署步骤（通用）

### 1) 创建虚拟环境并安装依赖

在 `d:\Github\brand-dashboard\api\` 目录执行：

```bash
uv sync
```

开发依赖（含测试）：

```bash
uv sync --extra dev
```

### 2) 初始化 MySQL 数据库

参见 [database/README.md](file:///d:/Github/brand-dashboard/api/database/README.md) 的初始化步骤。常用命令如下（示例以数据库名 `geo` 为例）：

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS geo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p geo < database/schema.sql
mysql -u root -p geo -e "SHOW TABLES;"
```

### 3) 配置数据库连接（推荐使用 api/.env）

服务在启动时会尝试加载 `api/.env`（路径：`d:\Github\brand-dashboard\api\.env`）。可写入以下内容：

```bash
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=devpassword
DB_NAME=geo
DB_CHARSET=utf8mb4
```

说明：

- 以上环境变量由 [database.py](file:///d:/Github/brand-dashboard/api/v1/repositories/database.py) 使用。
- 若未提供 `.env`，则使用代码中的默认值（不建议用于生产）。

### 4) 配置 LLM（可选）

默认从 `api/config/llm_settings.json` 读取 LLM 配置。

- 示例文件：`api/config/llm_settings.json`
- 字段说明：见 [config/README.md](file:///d:/Github/brand-dashboard/api/config/README.md)

生产环境建议将 `api_key` 通过更安全的方式管理（例如环境变量/密钥管理系统），避免把真实密钥写入仓库文件。

### 5) 启动服务

在 `d:\Github\brand-dashboard\api\` 目录运行：

- 开发模式（自动 reload）

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- 也可直接运行模块入口（等价于启用 reload 的 uvicorn）

```bash
python -m api.main
```

启动后验证：

```bash
curl http://localhost:8000/api/v1/health
```

并访问：

- http://localhost:8000/api/v1/docs

## 生产化部署建议（Linux）

### 1) 使用多进程 worker

在 CPU 核数允许时，可启用多个 worker（示例为 4）：

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2) systemd 托管（示例）

示例服务文件（路径建议：`/etc/systemd/system/brand-dashboard-api.service`）：

```ini
[Unit]
Description=Brand Dashboard API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/brand-dashboard/api
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/brand-dashboard/api/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用与启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable brand-dashboard-api
sudo systemctl start brand-dashboard-api
sudo systemctl status brand-dashboard-api
```

### 3) Nginx 反向代理（示例）

将外部流量转发到 8000（示例仅供参考）：

```nginx
server {
  listen 80;
  server_name your-domain.example.com;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

如需启用 HTTPS，请按常规方式配置证书与 `listen 443 ssl`。

## 常见问题排查

### 1) 启动时报错：ModuleNotFoundError

原因：依赖未正确安装。执行：

```bash
uv sync
```

### 2) 数据库连接失败

- 检查 MySQL 是否可达（host/port）、账号密码与库名是否正确
