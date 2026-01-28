# Web 前端 Docker 容器化部署文档

本文档详细说明如何使用 Docker 容器构建和部署 Brand Dashboard 的前端项目。

## 1. 环境准备

*   **Docker Engine**: 20.10.0 或更高版本
*   **Docker Compose** (可选): 用于编排服务

## 2. Docker 镜像构建

项目根目录下 `web/Dockerfile.prod` 文件已经定义了多阶段构建流程：
1.  **Build Stage**: 使用 Node.js 环境构建前端静态资源。
2.  **Production Stage**: 使用 Nginx 镜像服务静态资源。

### 2.1 构建镜像

在 `web` 目录下执行以下命令：

```bash
cd web
# 构建镜像，标签为 brand-dashboard-web
docker build -f Dockerfile.prod -t brand-dashboard-web .
```

构建成功后，可以使用 `docker images` 查看镜像。

## 3. 运行容器

### 3.1 使用 Docker CLI 运行

如果您单独运行前端容器，需要确保它能访问到后端服务。

**场景 A：后端也在 Docker 容器中运行 (推荐)**
假设后端容器名为 `api`，且并在同一个 Docker 网络中。

```bash
# 1. 创建网络 (如果还没有)
docker network create brand-net

# 2. 运行前端容器
docker run -d \
  --name brand-web \
  --network brand-net \
  -p 80:80 \
  brand-dashboard-web
```

**注意**: `web/nginx.conf` 默认配置了 `proxy_pass http://api:8000;`。这意味着在 Docker 网络中，后端服务的容器名称（或服务别名）必须是 `api`。

**场景 B：后端在宿主机运行 (http://localhost:8000)**
如果后端直接运行在宿主机上，您需要修改容器内的 Nginx 配置，或者使用 host 网络模式（仅限 Linux）。

```bash
# 使用 host 网络模式 (Linux)
docker run -d \
  --name brand-web \
  --network host \
  brand-dashboard-web
```
或者，如果在 Mac/Windows 上，可以使用 `host.docker.internal` 替换 `nginx.conf` 中的 `api`，但这需要修改配置文件并重新构建镜像。

### 3.2 使用 Docker Compose (推荐)

在项目根目录（通常包含 `api` 和 `web` 目录的上一级）创建一个 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  # 后端服务
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    networks:
      - brand-net

  # 前端服务
  web:
    build:
      context: ./web
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    depends_on:
      - api
    networks:
      - brand-net

networks:
  brand-net:
    driver: bridge
```

启动服务：
```bash
docker-compose up -d --build
```

## 4. Nginx 配置说明

容器内部使用了 `web/nginx.conf` 作为配置文件。

关键配置项说明：
*   **root /usr/share/nginx/html**: 静态文件存放位置（由 `Dockerfile.prod` 复制进去）。
*   **try_files $uri $uri/ /index.html**: 支持 React Router 的 History 模式，防止刷新页面 404。
*   **location /api**: 反向代理设置。默认指向 `http://api:8000`。

如果需要自定义 Nginx 配置（例如修改后端地址），可以修改 `web/nginx.conf` 然后重新构建镜像。

## 5. 常见运维操作

*   **查看日志**:
    ```bash
    docker logs -f brand-web
    ```

*   **停止与删除容器**:
    ```bash
    docker stop brand-web
    docker rm brand-web
    ```

*   **更新部署**:
    1.  拉取最新代码。
    2.  重新构建镜像：`docker build -f Dockerfile.prod -t brand-dashboard-web .`
    3.  停止并删除旧容器。
    4.  启动新容器。
