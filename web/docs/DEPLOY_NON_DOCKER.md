# Web 前端非 Docker 生产环境部署文档

本文档详细说明如何在不使用 Docker 容器的情况下，在 Linux 服务器（如 Ubuntu/CentOS）上部署 Brand Dashboard 的前端项目。

## 1. 环境准备

在开始部署之前，请确保服务器满足以下要求：

*   **Node.js**: v18.0.0 或更高版本 (用于构建项目)
*   **Nginx**: 最新稳定版 (用于作为 Web 服务器和反向代理)
*   **Git**: 用于拉取代码 (可选)

### 安装 Node.js (以 Ubuntu 为例)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
# 验证安装
node -v
npm -v
```

### 安装 Nginx (以 Ubuntu 为例)
```bash
sudo apt update
sudo apt install nginx
# 验证安装
nginx -v
```

## 2. 获取代码与构建

1.  **拉取代码** (假设部署在 `/var/www/brand-dashboard` 目录)
    ```bash
    mkdir -p /var/www/brand-dashboard
    cd /var/www/brand-dashboard
    # 这里的 git clone 仅为示例，请根据实际情况上传代码或拉取
    git clone <repository-url> .
    ```

2.  **安装依赖与构建**
    进入 `web` 目录进行构建：
    ```bash
    cd web
    # 安装依赖
    npm install

    # 执行构建
    npm run build
    ```

3.  **验证构建产物**
    构建完成后，会在 `web` 目录下生成 `dist` 文件夹。此文件夹包含了所有静态资源（HTML, CSS, JS）。
    ```bash
    ls -l dist/
    # 应包含 index.html 和 assets 目录
    ```

## 3. Nginx 配置

我们需要配置 Nginx 来服务静态文件，并将 API 请求转发到后端服务。

1.  **创建 Nginx 配置文件**
    ```bash
    sudo nano /etc/nginx/sites-available/brand-dashboard
    ```

2.  **写入以下配置**
    请根据实际情况修改 `server_name` 和 `root` 路径。

    ```nginx
    server {
        listen 80;
        server_name your-domain.com; # 替换为你的域名或 IP

        # 前端静态文件根目录
        root /var/www/brand-dashboard/web/dist;
        index index.html;

        # 开启 gzip 压缩 (可选，建议开启)
        gzip on;
        gzip_min_length 1k;
        gzip_comp_level 6;
        gzip_types text/plain text/css text/javascript application/json application/javascript application/x-javascript application/xml;

        # 处理前端路由 (SPA 必须配置)
        location / {
            try_files $uri $uri/ /index.html;
        }

        # 静态资源缓存配置 (可选)
        location /assets/ {
            expires 7d;
            access_log off;
        }

        # API 反向代理
        # 假设后端运行在同一台服务器的 8000 端口
        location /api {
            proxy_pass http://localhost:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 错误页面处理
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
    ```

3.  **启用配置**
    ```bash
    sudo ln -s /etc/nginx/sites-available/brand-dashboard /etc/nginx/sites-enabled/
    # 检查配置语法是否正确
    sudo nginx -t
    ```

4.  **重启 Nginx**
    ```bash
    sudo systemctl restart nginx
    ```

## 4. 后续维护

*   **更新代码**:
    ```bash
    cd /var/www/brand-dashboard
    git pull
    cd web
    npm install
    npm run build
    # Nginx 通常不需要重启，除非修改了 Nginx 配置
    ```

*   **常见问题**:
    *   **404 Not Found**: 检查 Nginx 配置中的 `root` 路径是否正确指向了 `dist` 目录。
    *   **刷新页面 404**: 确保配置了 `try_files $uri $uri/ /index.html;`。
    *   **API 请求失败**: 检查后端服务是否启动，以及 `proxy_pass` 地址是否正确。
