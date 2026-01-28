# Web 项目生产环境部署文档 (非 Docker 容器化部署)

本文档详细说明如何在生产环境服务器（如 CentOS, Ubuntu 等 Linux 发行版）上部署 Brand Analysis Dashboard 项目。

## 1. 环境准备

在开始部署前，请确保服务器已安装以下基础环境：

### 1.1 系统基础
- 操作系统: Linux (推荐 Ubuntu 22.04 LTS 或 CentOS 7+)
- Git
- Nginx (用于前端静态资源托管及反向代理)

### 1.2 后端依赖
- Python: 3.13+ (推荐使用 pyenv 或系统包管理器安装)
- MySQL: 8.0+

### 1.3 前端依赖
- Node.js: 18+ (推荐使用 nvm 管理)
- npm: 随 Node.js 安装

---

## 2. 数据库部署

1. **登录 MySQL 数据库**
   ```bash
   mysql -u root -p
   ```

2. **创建数据库**
   ```sql
   CREATE DATABASE brand_dashboard DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **导入数据表结构**
   将项目中的 SQL 文件上传至服务器，并按顺序执行导入：
   ```bash
   # 假设源码在 /opt/brand-dashboard
   cd /opt/brand-dashboard/api/database
   
   mysql -u root -p brand_dashboard < init.sql
   mysql -u root -p brand_dashboard < database_schema.sql
   mysql -u root -p brand_dashboard < schema_tenants_and_users.sql
   ```

---

## 3. 后端 (API) 部署

### 3.1 获取代码
将项目代码克隆到服务器目录，例如 `/opt/brand-dashboard`。

### 3.2 创建虚拟环境
建议使用 Python 虚拟环境隔离依赖。

```bash
cd /opt/brand-dashboard
python3 -m venv venv
source venv/bin/activate
```

### 3.3 安装依赖
```bash
pip install --upgrade pip
pip install -r api/requirements.txt
```

### 3.4 配置环境变量
后端连接数据库需要配置环境变量。您可以创建一个 `.env` 文件或直接在启动脚本中指定。
建议在 `/opt/brand-dashboard/api/.env` 创建配置文件（需确保代码支持加载 .env，或通过 export 导出）：

```bash
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password
export DB_NAME=brand_dashboard
export DB_CHARSET=utf8mb4
```

### 3.5 使用 Systemd 管理进程
创建 Systemd 服务文件以确保服务后台运行及开机自启。

创建文件 `/etc/systemd/system/brand-api.service`:

```ini
[Unit]
Description=Brand Dashboard API Service
After=network.target mysql.service

[Service]
User=root
WorkingDirectory=/opt/brand-dashboard
Environment="PATH=/opt/brand-dashboard/venv/bin"
Environment="DB_HOST=127.0.0.1"
Environment="DB_PORT=3306"
Environment="DB_USER=your_db_user"
Environment="DB_PASSWORD=your_db_password"
Environment="DB_NAME=brand_dashboard"
Environment="DB_CHARSET=utf8mb4"
ExecStart=/opt/brand-dashboard/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start brand-api
sudo systemctl enable brand-api
sudo systemctl status brand-api
```

---

## 4. 前端 (Web) 部署

### 4.1 编译构建

在本地或构建服务器上进行构建（也可在生产服务器构建，但建议分离）。

```bash
cd /opt/brand-dashboard/web
npm install
npm run build
```

构建完成后，会生成 `dist` 目录，这就是我们需要部署的静态文件。

### 4.2 配置 Nginx

编辑 Nginx 配置文件（通常位于 `/etc/nginx/sites-available/default` 或 `/etc/nginx/conf.d/brand-dashboard.conf`）。

```nginx
server {
    listen 80;
    server_name your-domain.com; # 请替换为实际域名或 IP

    # 前端静态资源
    location / {
        root /opt/brand-dashboard/web/dist;
        index index.html index.htm;
        try_files $uri $uri/ /index.html; # 支持 React Router History 模式
    }

    # 后端 API 反向代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 错误页面
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

### 4.3 重启 Nginx
验证配置并重启：
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. 验证部署

1. **访问前端**: 打开浏览器访问 `http://your-domain.com` 或服务器 IP。
2. **测试接口**: 确保前端页面能正常加载数据，查看网络请求 `/api/...` 是否返回 200 状态码。
3. **查看日志**:
   - 后端日志: `journalctl -u brand-api -f`
   - Nginx 日志: `/var/log/nginx/error.log`

## 6. 维护与更新

- **后端更新**:
  ```bash
  cd /opt/brand-dashboard
  git pull
  source venv/bin/activate
  pip install -r api/requirements.txt # 如果有依赖更新
  sudo systemctl restart brand-api
  ```

- **前端更新**:
  ```bash
  cd /opt/brand-dashboard/web
  git pull
  npm install
  npm run build
  # 静态文件无需重启 Nginx，即刻生效
  ```
