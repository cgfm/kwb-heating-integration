# KWB Development Helper Script
# Provides common development tasks for KWB Heating Integration

param(
    [Parameter(Position=0)]
    [string]$Action = "help"
)

function Show-Help {
    Write-Host ""
    Write-Host "🔧 KWB Development Helper" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available actions:" -ForegroundColor Yellow
    Write-Host "  reset-kwb      Reset only KWB integration (keep HA running)" -ForegroundColor Green
    Write-Host "  reset-full     Full HA reset (stop container, delete config)" -ForegroundColor Green
    Write-Host "  restart        Restart HA container" -ForegroundColor Green
    Write-Host "  logs           Show recent HA logs" -ForegroundColor Green
    Write-Host "  logs-kwb       Show KWB-specific logs" -ForegroundColor Green
    Write-Host "  status         Show container status" -ForegroundColor Green
    Write-Host "  open           Open HA web interface" -ForegroundColor Green
    Write-Host "  backup-config  Backup current HA config" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\dev-helper.ps1 <action>" -ForegroundColor Cyan
    Write-Host "Example: .\dev-helper.ps1 reset-kwb" -ForegroundColor Cyan
}

function Reset-KWB {
    Write-Host "🔄 Resetting KWB integration..." -ForegroundColor Yellow
    
    # Check if container is running
    $containerStatus = docker ps --filter "name=kwb-hass-test" --format "{{.Status}}"
    if (-not $containerStatus) {
        Write-Host "❌ Container kwb-hass-test is not running" -ForegroundColor Red
        return
    }
    
    Write-Host "1️⃣ Removing KWB integration config..." -ForegroundColor Cyan
    docker exec kwb-hass-test rm -f /config/.storage/core.config_entries
    docker exec kwb-hass-test rm -rf /config/.storage/kwb_heating*
    docker exec kwb-hass-test rm -f /config/configuration.yaml
    
    Write-Host "2️⃣ Restarting Home Assistant..." -ForegroundColor Cyan
    docker restart kwb-hass-test
    
    Write-Host "✅ KWB integration reset completed!" -ForegroundColor Green
    Write-Host "💡 You can now reconfigure the integration in HA UI" -ForegroundColor Blue
    Write-Host "🌐 Opening HA web interface in 30 seconds..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    Start-Process "http://localhost:8123"
}

function Reset-Full {
    Write-Host "🔄 Full HA reset..." -ForegroundColor Yellow
    
    Write-Host "1️⃣ Stopping container..." -ForegroundColor Cyan
    docker stop kwb-hass-test
    
    Write-Host "2️⃣ Removing container..." -ForegroundColor Cyan
    docker rm kwb-hass-test
    
    Write-Host "3️⃣ Cleaning up config directory..." -ForegroundColor Cyan
    if (Test-Path "./ha-config") {
        Remove-Item "./ha-config" -Recurse -Force
        Write-Host "   ✅ Config directory removed" -ForegroundColor Green
    }
    
    Write-Host "4️⃣ Recreating container..." -ForegroundColor Cyan
    docker run -d --name kwb-hass-test -p 8123:8123 -v "${PWD}/ha-config:/config" -v "${PWD}/custom_components:/config/custom_components" homeassistant/home-assistant:latest
    
    Write-Host "✅ Full HA reset completed!" -ForegroundColor Green
    Write-Host "💡 HA is starting up, this may take a few minutes..." -ForegroundColor Blue
}

function Restart-Container {
    Write-Host "🔄 Restarting HA container..." -ForegroundColor Yellow
    docker restart kwb-hass-test
    Write-Host "✅ Container restarted!" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "📋 Recent HA logs..." -ForegroundColor Cyan
    docker logs kwb-hass-test --tail 50
}

function Show-KWBLogs {
    Write-Host "📋 KWB-specific logs..." -ForegroundColor Cyan
    docker logs kwb-hass-test 2>&1 | Select-String -Pattern "kwb|KWB" -Context 1
}

function Show-Status {
    Write-Host "📊 Container status..." -ForegroundColor Cyan
    docker ps --filter "name=kwb-hass-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host ""
    Write-Host "📊 HA Health Check..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8123" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ HA Web Interface is accessible" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ HA Web Interface not accessible" -ForegroundColor Red
    }
}

function Open-HA {
    Write-Host "🌐 Opening HA web interface..." -ForegroundColor Cyan
    Start-Process "http://localhost:8123"
}

function Backup-Config {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = ".\ha-config-backup-$timestamp"
    
    if (Test-Path "./ha-config") {
        Write-Host "💾 Backing up HA config to $backupPath..." -ForegroundColor Cyan
        Copy-Item "./ha-config" -Destination $backupPath -Recurse
        Write-Host "✅ Config backed up!" -ForegroundColor Green
    } else {
        Write-Host "❌ No config directory found" -ForegroundColor Red
    }
}

# Main script logic
switch ($Action.ToLower()) {
    "reset-kwb" { Reset-KWB }
    "reset-full" { Reset-Full }
    "restart" { Restart-Container }
    "logs" { Show-Logs }
    "logs-kwb" { Show-KWBLogs }
    "status" { Show-Status }
    "open" { Open-HA }
    "backup-config" { Backup-Config }
    "help" { Show-Help }
    default { 
        Write-Host "❌ Unknown action: $Action" -ForegroundColor Red
        Show-Help 
    }
}
