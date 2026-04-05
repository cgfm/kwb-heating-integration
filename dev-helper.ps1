# KWB Development Helper Script (PowerShell)
# Provides common development tasks for KWB Heating Integration

param(
    [Parameter(Position = 0)]
    [ValidateSet(
        "start", "stop", "restart", "status",
        "reset-kwb", "reset-full",
        "logs", "logs-kwb", "open",
        "backup-config", "completion", "no-completion",
        "help"
    )]
    [string]$Action = "help"
)

$ContainerName = "kwb-hass-test"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Show-Help {
    Write-Host ""
    Write-Host "  KWB Development Helper" -ForegroundColor Cyan
    Write-Host "  =========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Container:" -ForegroundColor Yellow
    Write-Host "    start          " -ForegroundColor Green -NoNewline; Write-Host "Start HA container"
    Write-Host "    stop           " -ForegroundColor Green -NoNewline; Write-Host "Stop HA container"
    Write-Host "    restart        " -ForegroundColor Green -NoNewline; Write-Host "Restart HA container"
    Write-Host "    status         " -ForegroundColor Green -NoNewline; Write-Host "Show container status"
    Write-Host ""
    Write-Host "  Reset:" -ForegroundColor Yellow
    Write-Host "    reset-kwb      " -ForegroundColor Green -NoNewline; Write-Host "Reset only KWB integration (keep HA running)"
    Write-Host "    reset-full     " -ForegroundColor Green -NoNewline; Write-Host "Full HA reset (stop container, delete config)"
    Write-Host ""
    Write-Host "  Logs & UI:" -ForegroundColor Yellow
    Write-Host "    logs           " -ForegroundColor Green -NoNewline; Write-Host "Show recent HA logs"
    Write-Host "    logs-kwb       " -ForegroundColor Green -NoNewline; Write-Host "Show KWB-specific logs"
    Write-Host "    open           " -ForegroundColor Green -NoNewline; Write-Host "Open HA web interface"
    Write-Host ""
    Write-Host "  Utilities:" -ForegroundColor Yellow
    Write-Host "    backup-config  " -ForegroundColor Green -NoNewline; Write-Host "Backup current HA config"
    Write-Host "    completion     " -ForegroundColor Green -NoNewline; Write-Host "Add tab completion to PowerShell profile"
    Write-Host "    no-completion  " -ForegroundColor Green -NoNewline; Write-Host "Remove tab completion from PowerShell profile"
    Write-Host ""
    Write-Host "  Usage: .\dev-helper.ps1 <action>" -ForegroundColor Cyan
    Write-Host "  Example: .\dev-helper.ps1 reset-kwb" -ForegroundColor Cyan
}

function Test-ContainerRunning {
    $status = docker ps --filter "name=$ContainerName" --format "{{.Status}}" 2>$null
    return [bool]$status
}

function Start-HAContainer {
    Write-Host "  Starting HA container..." -ForegroundColor Yellow
    docker compose -f "$ScriptDir/docker-compose.yml" up -d
    Write-Host "  Container started!" -ForegroundColor Green
}

function Stop-HAContainer {
    Write-Host "  Stopping HA container..." -ForegroundColor Yellow
    docker compose -f "$ScriptDir/docker-compose.yml" down --remove-orphans 2>$null
    if ($LASTEXITCODE -ne 0) {
        docker stop $ContainerName 2>$null
    }
    Write-Host "  Container stopped!" -ForegroundColor Green
}

function Restart-HAContainer {
    Write-Host "  Restarting HA container..." -ForegroundColor Yellow
    docker compose -f "$ScriptDir/docker-compose.yml" restart
    Write-Host "  Container restarted!" -ForegroundColor Green
}

function Reset-KWB {
    Write-Host "  Resetting KWB integration..." -ForegroundColor Yellow

    if (-not (Test-ContainerRunning)) {
        Write-Host "  Container $ContainerName is not running" -ForegroundColor Red
        return
    }

    Write-Host "  1. Removing KWB integration config..." -ForegroundColor Cyan
    docker exec $ContainerName rm -f /config/.storage/core.config_entries
    docker exec $ContainerName rm -rf /config/.storage/kwb_heating*
    docker exec $ContainerName rm -f /config/configuration.yaml

    Write-Host "  2. Restarting Home Assistant..." -ForegroundColor Cyan
    docker restart $ContainerName

    Write-Host "  KWB integration reset completed!" -ForegroundColor Green
    Write-Host "  You can now reconfigure the integration in HA UI" -ForegroundColor Blue
    Write-Host "  Opening HA web interface in 30 seconds..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    Start-Process "http://localhost:8123"
}

function Reset-Full {
    Write-Host "  Full HA reset..." -ForegroundColor Yellow

    Write-Host "  1. Stopping and removing container..." -ForegroundColor Cyan
    docker compose -f "$ScriptDir/docker-compose.yml" down --remove-orphans 2>$null
    docker rm -f $ContainerName 2>$null

    Write-Host "  2. Cleaning up config directory..." -ForegroundColor Cyan
    $configPath = Join-Path $ScriptDir "ha-config"
    if (Test-Path $configPath) {
        Remove-Item -Recurse -Force $configPath
        Write-Host "     Config directory removed" -ForegroundColor Green
    }

    Write-Host "  3. Recreating container..." -ForegroundColor Cyan
    docker compose -f "$ScriptDir/docker-compose.yml" up -d

    Write-Host "  4. Waiting for Home Assistant to start..." -ForegroundColor Cyan
    $retries = 0
    while ($retries -lt 60) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8123" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            break
        } catch {
            Start-Sleep -Seconds 5
            $retries++
            Write-Host "     Waiting... ($retries/60)"
        }
    }

    if ($retries -ge 60) {
        Write-Host "  Home Assistant did not start in time" -ForegroundColor Red
        return
    }
    Write-Host "     Home Assistant is up" -ForegroundColor Green

    Write-Host "  Full HA reset completed!" -ForegroundColor Green
    Write-Host "  Custom component is mounted via docker volume, ready to configure." -ForegroundColor Blue
}

function Show-Logs {
    Write-Host "  Recent HA logs..." -ForegroundColor Cyan
    docker logs $ContainerName --tail 50
}

function Show-KWBLogs {
    Write-Host "  KWB-specific logs..." -ForegroundColor Cyan
    $logs = docker logs $ContainerName 2>&1 | Select-String -Pattern "kwb" -Context 1
    if ($logs) {
        $logs | ForEach-Object { Write-Host $_ }
    } else {
        Write-Host "  No KWB logs found" -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "  Container status..." -ForegroundColor Cyan
    docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    Write-Host ""
    Write-Host "  HA Health Check..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8123" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "  HA Web Interface is accessible" -ForegroundColor Green
    } catch {
        Write-Host "  HA Web Interface not accessible" -ForegroundColor Red
    }
}

function Open-HA {
    Write-Host "  Opening HA web interface..." -ForegroundColor Cyan
    Start-Process "http://localhost:8123"
}

function Backup-Config {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $ScriptDir "ha-config-backup-$timestamp"
    $configPath = Join-Path $ScriptDir "ha-config"

    if (Test-Path $configPath) {
        Write-Host "  Backing up HA config to $backupPath..." -ForegroundColor Cyan
        Copy-Item -Recurse $configPath $backupPath
        Write-Host "  Config backed up!" -ForegroundColor Green
    } else {
        Write-Host "  No config directory found" -ForegroundColor Red
    }
}

function Install-Completion {
    $profilePath = $PROFILE.CurrentUserAllHosts
    $completionBlock = @"

# KWB dev-helper tab completion
Register-ArgumentCompleter -CommandName '.\dev-helper.ps1', 'dev-helper.ps1' -ParameterName Action -ScriptBlock {
    param(`$cmd, `$param, `$wordToComplete)
    @('start','stop','restart','status','reset-kwb','reset-full','logs','logs-kwb','open','backup-config','completion','no-completion','help') |
        Where-Object { `$_ -like "`$wordToComplete*" } |
        ForEach-Object { [System.Management.Automation.CompletionResult]::new(`$_) }
}
"@

    if ((Test-Path $profilePath) -and (Get-Content $profilePath -Raw) -match "KWB dev-helper tab completion") {
        Write-Host "  Tab completion is already installed in $profilePath" -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path (Split-Path $profilePath))) {
        New-Item -ItemType Directory -Path (Split-Path $profilePath) -Force | Out-Null
    }

    Add-Content -Path $profilePath -Value $completionBlock
    Write-Host "  Tab completion added to $profilePath" -ForegroundColor Green
    Write-Host "  Open a new terminal or run '. `$PROFILE' to activate." -ForegroundColor Blue
}

function Remove-Completion {
    $profilePath = $PROFILE.CurrentUserAllHosts

    if (-not (Test-Path $profilePath)) {
        Write-Host "  Tab completion is not installed in $profilePath" -ForegroundColor Yellow
        return
    }

    $content = Get-Content $profilePath -Raw
    if ($content -notmatch "KWB dev-helper tab completion") {
        Write-Host "  Tab completion is not installed in $profilePath" -ForegroundColor Yellow
        return
    }

    $cleaned = $content -replace '(?s)\r?\n# KWB dev-helper tab completion\r?\nRegister-ArgumentCompleter.*?\r?\n}\r?\n', ''
    Set-Content -Path $profilePath -Value $cleaned.TrimEnd()
    Write-Host "  Tab completion removed from $profilePath" -ForegroundColor Green
    Write-Host "  Open a new terminal or run '. `$PROFILE' to apply." -ForegroundColor Blue
}

# Main script logic
switch ($Action) {
    "start"         { Start-HAContainer }
    "stop"          { Stop-HAContainer }
    "restart"       { Restart-HAContainer }
    "reset-kwb"     { Reset-KWB }
    "reset-full"    { Reset-Full }
    "logs"          { Show-Logs }
    "logs-kwb"      { Show-KWBLogs }
    "status"        { Show-Status }
    "open"          { Open-HA }
    "backup-config" { Backup-Config }
    "completion"    { Install-Completion }
    "no-completion" { Remove-Completion }
    "help"          { Show-Help }
    default         { Show-Help }
}
