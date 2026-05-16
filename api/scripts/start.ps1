$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$VenvPath = Join-Path $ProjectRoot ".venv"
$RequirementsPath = Join-Path $ProjectRoot "requirements.txt"

# 1. 激活项目级虚拟环境（如果存在）
if (Test-Path $VenvPath) {
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    . $ActivateScript
    Write-Host "Activated project virtual environment: $VenvPath" -ForegroundColor Cyan
} else {
    Write-Host "Using current Python environment (no project .venv found)" -ForegroundColor Yellow
}

# 2. 安装依赖
if (Test-Path $RequirementsPath) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    pip install -r $RequirementsPath --quiet
    pip install python-dotenv asgi-correlation-id --quiet
}

# 3. 切换到项目根目录并启动
Set-Location $ProjectRoot
Write-Host "Starting API server (non-container mode)..." -ForegroundColor Green
Write-Host "  Dialect: sqlite (from api/.env)" -ForegroundColor Yellow
Write-Host "  Swagger: http://localhost:8000/api/v1/docs" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop`n" -ForegroundColor Gray

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000