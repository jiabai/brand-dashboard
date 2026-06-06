param(
    [switch]$StopOnFirstError,
    [switch]$PylintFull,
    [string]$Python = "python"
)

# Ensure we are running from the project root
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path $ScriptDir -Parent
Set-Location $ProjectRoot

$ErrorActionPreference = "Stop"
$hadFailure = $false
$skipped = New-Object System.Collections.Generic.List[string]

function Test-Cmd([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PythonModule([string]$Module) {
    if (-not (Test-Cmd $Python)) {
        throw "Python executable not found: $Python"
    }
    & $Python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$Module') else 1)" | Out-Null
    return $LASTEXITCODE -eq 0
}

function Run-Step([string]$Name, [string]$Exe, [string[]]$Arguments) {
    Write-Host "==> $Name"
    & $Exe @Arguments
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "FAIL ($code): $Name" -ForegroundColor Red
        $script:hadFailure = $true
        if ($StopOnFirstError) {
            exit $code
        }
        return
    }
    Write-Host "OK: $Name" -ForegroundColor Green
}

function Run-PythonModule([string]$Name, [string]$Module, [string[]]$Arguments) {
    Run-Step $Name $Python (@("-m", $Module) + $Arguments)
}

function Run-PythonModuleIfPresent([string]$Name, [string]$Module, [string[]]$Arguments) {
    if (-not (Test-PythonModule $Module)) {
        $script:skipped.Add("$Name (missing python module: $Module)") | Out-Null
        return
    }
    Run-PythonModule $Name $Module $Arguments
}

function Get-PythonFiles() {
    if (Test-Cmd "git") {
        $files = & git ls-files -- "*.py"
        if ($LASTEXITCODE -eq 0 -and $files) {
            return $files
        }
    }
    return Get-ChildItem -Path "src", "tests" -Recurse -Filter *.py | ForEach-Object { $_.FullName }
}

Run-PythonModuleIfPresent "black (check)" "black" @("--check", "src", "tests")
Run-PythonModuleIfPresent "isort (check-only)" "isort" @("--check-only", "src", "tests")
Run-PythonModuleIfPresent "flake8" "flake8" @("src", "tests")
Run-PythonModuleIfPresent "ruff" "ruff" @("check", "src", "tests")
if (Test-PythonModule "pylint") {
    if ($PylintFull) {
        Run-PythonModule "pylint" "pylint" @("src", "tests")
    } else {
        Run-PythonModule "pylint (errors-only)" "pylint" @("--errors-only", "src", "tests")
    }
} else {
    $script:skipped.Add("pylint (missing python module: pylint)") | Out-Null
}

$pyFiles = Get-PythonFiles
if ($pyFiles -and (Test-PythonModule "pyupgrade")) {
    $pyupgradeHelp = & $Python -m pyupgrade --help 2>&1 | Out-String
    if ($pyupgradeHelp -match "(^|\\s)--diff(\\s|$)") {
        Run-PythonModule "pyupgrade (diff)" "pyupgrade" (@("--py38-plus", "--diff") + $pyFiles)
    } else {
        $skipped.Add("pyupgrade (--diff unsupported)") | Out-Null
    }
} else {
    if (-not (Test-PythonModule "pyupgrade")) {
        $skipped.Add("pyupgrade (missing python module: pyupgrade)") | Out-Null
    }
}

Run-PythonModuleIfPresent "radon cc" "radon" @("cc", "src", "-a")

if (Test-Cmd "npx.cmd" -or Test-Cmd "npx") {
    $npxExe = if (Test-Cmd "npx.cmd") { "npx.cmd" } else { "npx" }
    & $npxExe --yes prettier --version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Run-Step "prettier (check)" $npxExe @("--yes", "prettier", "--check", "**/*.{md,json,yml,yaml}", "--ignore-unknown")
    } else {
        $skipped.Add("prettier (npx prettier unavailable)") | Out-Null
    }
} else {
    $skipped.Add("prettier (missing command: npx)") | Out-Null
}

if ($skipped.Count -gt 0) {
    Write-Host ""
    Write-Host "Skipped:" -ForegroundColor Yellow
    $skipped | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
}

if ($hadFailure) {
    exit 1
}
exit 0

