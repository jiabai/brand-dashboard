# Web 项目生产环境部署文档 (Docker 容器化部署)

本文档详细说明如何使用 Docker 和 Docker Compose 在生产环境中快速部署 Brand Analysis Dashboard 项目。

## 1. 环境准备

请确保服务器已安装以下软件：

- **Docker Engine**: 20.10+
- **Docker Compose**: 2.0+

检查安装：
```bash
docker --version
docker compose version
```

---

## 2. 部署配置

项目根目录下提供了生产环境专用的 Compose 配置文件 `docker-compose.prod.yml`。

### 2.1 数据库配置
在启动前，请根据实际生产环境修改 `docker-compose.prod.yml` 中的环境变量，或将敏感信息配置在 `.env` 文件中（推荐）。

**当前默认配置 (docker-compose.prod.yml):**
```yaml
services:
  api:
    environment:
      - DB_HOST=192.168.31.233  # 生产环境 MySQL 地址
      - DB_PORT=3306
      - DB_USER=root            # 建议修改为非 root 用户
      - DB_PASSWORD=123456      # 务必修改为强密码
      - DB_NAME=geo
      - DB_CHARSET=utf8mb4
```

> **注意**: 默认配置未包含 MySQL 容器，假设您连接的是外部独立数据库或云数据库。如果需要容器化 MySQL，请在 compose 文件中添加 mysql 服务。

### 2.2 端口映射
默认端口映射如下，可根据需要调整：
- **Web 前端**: `8080` (宿主机) -> `80` (容器)
- **API 后端**: `8091` (宿主机) -> `8000` (容器)

---

## 3. 启动部署

在项目根目录下执行以下命令：

```bash
# 构建并后台启动服务
docker compose -f docker-compose.prod.yml up -d --build
```

### 常用管理命令

```bash
# 查看容器状态
docker compose -f docker-compose.prod.yml ps

# 查看日志 (实时)
docker compose -f docker-compose.prod.yml logs -f

# 停止服务
docker compose -f docker-compose.prod.yml down

# 重启某个服务 (例如 api)
docker compose -f docker-compose.prod.yml restart api
```

---

## 4. 架构说明

### 4.1 前端 (Web)
- **Dockerfile**: `web/Dockerfile.prod`
- **基础镜像**: `nginx:1.28.1-slim`
- **构建过程**: 
  1. 使用 `node:24.13.0-slim` 编译 React 代码。
  2. 将生成的 `dist/` 目录复制到 Nginx 容器。
  3. 使用自定义 `web/nginx.conf` 覆盖默认配置。
- **反向代理**: 容器内的 Nginx 已配置 `/api` 转发，请求会代理到 `http://api:8000`。

### 4.2 后端 (API)
- **Dockerfile**: `api/Dockerfile.prod`
- **基础镜像**: `python:3.13.5-slim`
- **运行用户**: `appuser` (非 root 安全运行)
- **启动命令**: 使用 `uvicorn` 启动 FastAPI 应用。

---

## 5. 验证部署

部署成功后，您可以通过以下地址访问：

1. **Web 访问**: `http://localhost:8080` (或服务器 IP:8080)
2. **API 接口**: `http://localhost:8091/docs` (Swagger UI)

如果页面无法加载，请检查：
1. 数据库连接是否正常（查看 api 容器日志）。
2. 防火墙是否开放了 8080 和 8091 端口。

---

## 6. 持续更新

当代码有更新时，执行以下步骤重新部署：

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建并重启容器
docker compose -f docker-compose.prod.yml up -d --build
```

此命令会自动检测变更，重新构建镜像并替换运行中的容器，实现平滑升级。
