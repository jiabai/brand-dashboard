$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$WebRoot = Join-Path $ProjectRoot "web"

# 1. 安装依赖
Write-Host "Installing dependencies..." -ForegroundColor Cyan
npm --prefix $WebRoot install --silent

# 2. 切换到 web 目录并启动
Set-Location $WebRoot
Write-Host "Starting Web dev server (non-container mode)..." -ForegroundColor Green
Write-Host "  URL: http://localhost:3000" -ForegroundColor Yellow
Write-Host "  API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop`n" -ForegroundColor Gray

npm run dev