param (
    [string]$BackendPath  = "C:\path\to\backend",
    [int]$DockerStartupTimeoutSeconds = 120
)

# =============================
# Docker Desktop helpers
# =============================
function Start-DockerDesktop {
    $dockerExe = "$Env:ProgramFiles\Docker\Docker\Docker Desktop.exe"

    if (-not (Test-Path $dockerExe)) {
        Write-Host "ERROR: Docker Desktop not found." -ForegroundColor Red
        exit 1
    }

    Write-Host "Starting Docker Desktop..." -ForegroundColor Cyan
    Start-Process -FilePath $dockerExe
}

function Wait-ForDocker {
    $startTime = Get-Date

    while ($true) {
        try {
            docker info > $null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Docker is ready." -ForegroundColor Green
                return
            }
        } catch {}

        if ((Get-Date) - $startTime -gt [TimeSpan]::FromSeconds($DockerStartupTimeoutSeconds)) {
            Write-Host "ERROR: Docker did not become ready within timeout." -ForegroundColor Red
            exit 1
        }

        Start-Sleep -Seconds 3
    }
}

# =============================
# Compose helpers
# =============================
function Get-ComposeFile {
    param ([string]$Path)

    $files = @(
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml"
    )

    Push-Location $Path
    $file = $files | Where-Object { Test-Path $_ } | Select-Object -First 1
    Pop-Location

    if (-not $file) {
        Write-Host "ERROR: No Docker Compose file found in $Path" -ForegroundColor Red
        exit 1
    }

    return $file
}

function Start-Compose {
    param (
        [string]$Path,
        [string]$Name
    )

    Write-Host "Starting $Name..." -ForegroundColor Cyan
    Push-Location $Path
    docker compose up
    Pop-Location
}

function Stop-Compose {
    param (
        [string]$Path,
        [string]$Name
    )

    Write-Host "Stopping $Name..." -ForegroundColor Yellow
    Push-Location $Path
    docker compose down
    Pop-Location
}

# =============================
# Ensure Docker is running
# =============================
if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Start-DockerDesktop
}

Wait-ForDocker

# =============================
# Validate compose files
# =============================
Get-ComposeFile $FrontendPath | Out-Null
Get-ComposeFile $BackendPath  | Out-Null

# =============================
# Run both stacks
# =============================
try {
    # Backend first (usually provides APIs)
    Start-Job -ScriptBlock {
        param($Path)
        Set-Location $Path
        docker compose up
    } -ArgumentList $BackendPath | Out-Null

    Start-Sleep -Seconds 5

    Write-Host "Frontend and Backend are running. Press Ctrl+C or close the window to stop." -ForegroundColor Green

    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Stop-Compose $BackendPath  "Backend"
}
