# Dashboard 部署文档

本文档描述了如何在 Linux 服务器上部署 Dashboard 前端应用。

## 环境要求

- Node.js 20.x 或更高版本（推荐 LTS 版本）
- npm 10.x 或更高版本
- Linux 服务器（Ubuntu 20.04+ / CentOS 8+）

## 服务器准备

### 1. 安装 Node.js

**重要提示**：Node.js 18.x 已不再积极维护，建议使用 20.x 或更高版本。

```bash
# Ubuntu/Debian - 安装 Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL/Fedora - 安装 Node.js 20.x
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs  # 对于较新的 RHEL/CentOS/Fedora
# 或者
sudo yum install -y nodejs   # 对于较旧的版本

# 验证安装
node --version  # 应该显示 v20.x.x 或更高版本
npm --version   # 应该显示 10.x.x 或更高版本
```

**替代方案 - 使用 NodeSource N|Solid Runtime（可选）**：
```bash
# 安装 N|Solid Runtime（Node.js 的增强版本）
sudo dnf install nsolid -y
# 或
sudo yum install nsolid -y
```

### 2. 安装 PM2（进程管理器）

```bash
npm install -g pm2
```

### 3. 安装 Nginx（Web服务器）

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL/Fedora
sudo dnf install nginx  # 对于较新的版本
# 或者
sudo yum install nginx  # 对于较旧的版本

# 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 项目部署步骤

### 1. 上传项目文件

将项目文件上传到服务器，建议放在 `/var/www/` 目录下：

```bash
# 创建项目目录
sudo mkdir -p /var/www/dashboard
cd /var/www/dashboard

# 设置目录权限
sudo chown -R $USER:$USER /var/www/dashboard
sudo chmod -R 755 /var/www/dashboard

# 上传文件（使用scp或其他方式）
# 从本地上传到服务器
scp -r /path/to/local/dashboard user@your-server:/var/www/dashboard/

# 或者使用 git 克隆（如果项目有 git 仓库）
git clone your-repository-url .
```

### 2. 安装依赖

```bash
cd /var/www/dashboard

# 清理 npm 缓存（可选，如果遇到问题）
npm cache clean --force

# 安装项目依赖
npm install

# 验证安装是否成功
npm list --depth=0
```

### 3. 构建项目

```bash
# 构建生产版本
npm run build

# 构建完成后，文件会在 dist/dashboard 目录
# 检查构建结果
ls -la dist/dashboard/

# 如果构建失败，检查错误信息并确保所有依赖正确安装
# 可以尝试删除 node_modules 重新安装
# rm -rf node_modules package-lock.json
# npm install
```

### 4. 配置 Nginx

**重要说明**：`sites-available` 和 `sites-enabled` 目录是 Ubuntu/Debian 系统的标准做法，但 CentOS/RHEL/Fedora 系统默认使用不同的配置结构。

#### 对于 Ubuntu/Debian 系统：

创建 Nginx 配置文件：

```bash
sudo nano /etc/nginx/sites-available/dashboard
```

添加以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或IP

    root /var/www/dashboard/dist/dashboard;
    index index.html;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理配置（如果后端在同一服务器）
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

启用配置：

```bash
# 创建软链接（Ubuntu/Debian）
sudo ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 对于 CentOS/RHEL/Fedora 系统：

CentOS/RHEL/Fedora 默认没有 `sites-available` 和 `sites-enabled` 目录，需要直接编辑主配置文件或在 `conf.d` 目录中添加配置。

**方法1：直接创建在 conf.d 目录（推荐）**

创建配置文件：

```bash
sudo nano /etc/nginx/conf.d/dashboard.conf
```

添加以下配置内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或IP

    root /var/www/dashboard/dist/dashboard;
    index index.html;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理配置（如果后端在同一服务器）
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

**方法2：修改主配置文件**

如果需要，可以检查主配置文件是否包含 conf.d 目录：

```bash
sudo nano /etc/nginx/nginx.conf
# 在 http 块中确认包含以下语句
include /etc/nginx/conf.d/*.conf;
```

然后直接测试和重启：

```bash
# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 5. 使用 PM2 启动开发服务器（可选）

如果需要运行开发服务器：

```bash
# 安装依赖
npm install

# 使用 PM2 启动
pm2 start npm --name "dashboard" -- run dev

# 保存 PM2 配置
pm2 save
pm2 startup
```

### 6. 配置防火墙

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 环境变量配置

创建环境变量文件：

```bash
cd /var/www/dashboard
cp .env.example .env.production
```

编辑生产环境变量：

```bash
nano .env.production
```

常见配置项：

```env
VITE_API_URL=https://your-api-domain.com/api
VITE_APP_ENV=production
```

## SSL 证书配置（HTTPS）

### 使用 Let's Encrypt（推荐）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 部署验证

### 1. 检查服务状态

```bash
# 检查 Nginx
sudo systemctl status nginx

# 检查 PM2（如果使用）
pm2 status
```

### 2. 访问应用

- 浏览器访问：`http://your-domain.com`
- 检查控制台是否有错误
- 验证 API 调用是否正常

### 3. 性能检查

```bash
# 检查页面加载时间
curl -o /dev/null -s -w "%{time_total}\n" http://your-domain.com

# 检查静态资源缓存
curl -I http://your-domain.com/assets/main.js
```

## 常见问题解决

### 1. 404 错误（路由问题）

确保 Nginx 配置中包含：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 2. 权限问题

```bash
# 设置正确的文件权限
sudo chown -R www-data:www-data /var/www/dashboard
sudo chmod -R 755 /var/www/dashboard
```

### 3. 内存不足

```bash
# 检查内存使用
free -h

# 增加 swap（如果需要）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 4. 端口冲突

```bash
# 检查端口占用
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :3000
```

## 监控和维护

### 1. 日志查看

```bash
# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# PM2 日志（如果使用）
pm2 logs dashboard
```

### 2. 性能监控

```bash
# 系统资源
htop

# 磁盘空间
df -h

# 内存使用
free -h
```

### 3. 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建
npm run build

# 重启服务
sudo systemctl restart nginx
# 或
pm2 restart dashboard
```

## 安全建议

1. **定期更新系统和软件包**
2. **配置防火墙规则**
3. **使用强密码和SSH密钥**
4. **定期备份数据和配置**
5. **监控日志文件**
6. **及时更新SSL证书**

## 快速部署步骤（基于您的环境）

您的环境已经准备就绪：
- ✅ Node.js v22.20.0 - 完全兼容
- ✅ npm v11.6.2 - 版本合适

```bash
# 1. 安装 Nginx 和 PM2
sudo dnf install nginx -y
npm install -g pm2

# 2. 创建项目目录并上传文件
sudo mkdir -p /var/www/dashboard
cd /var/www/dashboard
# 上传您的项目文件...

# 3. 安装依赖并构建
npm install
npm run build

# 4. 配置 Nginx（CentOS/RHEL 方法）
sudo nano /etc/nginx/conf.d/dashboard.conf
# 将下面的配置内容粘贴到文件中

# 5. 测试配置并启动 Nginx
sudo nginx -t
sudo systemctl start nginx
sudo systemctl enable nginx

# 6. 配置防火墙
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**CentOS/RHEL Nginx 配置内容**：
```nginx
server {
    listen 80;
    server_name localhost;  # 或您的域名/IP

    root /var/www/dashboard/dist/dashboard;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

## 版本兼容性说明

**Node.js 版本选择**：
- ✅ **推荐**：Node.js 20.x LTS（长期支持版本）
- ✅ **可用**：Node.js 22.x（当前最新版本，如 v22.20.0）
- ⚠️ **警告**：Node.js 18.x 已停止积极维护，仅提供安全更新
- ❌ **避免**：Node.js 16.x 及更早版本（已结束生命周期）

**您的环境检查**：
- Node.js v22.20.0 ✅ - 完全兼容，性能优秀
- npm v11.6.2 ✅ - 版本合适，满足所有依赖需求

**为什么选择 Node.js 20+？**
- 获得官方长期支持直到 2026-04-30（20.x LTS）
- 更好的性能和安全性
- 支持最新的 JavaScript 特性
- 与 Vite 和现代前端工具更好的兼容性
- 改进的内存管理和错误处理

## 联系支持

如遇到部署问题，请检查：
1. 服务器日志文件
2. 浏览器控制台错误
3. 网络连接状态
4. 配置文件语法
5. Node.js 和 npm 版本兼容性

---

*最后更新：2024年12月*