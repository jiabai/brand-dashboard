$Port = 8000

# 1. 查找占用指定端口的进程
$Process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }

if (-not $Process) {
    Write-Host "No process found on port $Port (already stopped)" -ForegroundColor Yellow
    exit 0
}

# 2. 停止进程
$ProcessName = $Process.ProcessName
$ProcessId = $Process.Id
Write-Host "Stopping $ProcessName (PID: $ProcessId) on port $Port..." -ForegroundColor Cyan
Stop-Process -Id $ProcessId
Write-Host "Stopped successfully" -ForegroundColor Green