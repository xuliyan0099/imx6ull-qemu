@echo off
setlocal
for /f "usebackq delims=" %%i in (`wsl -d Ubuntu-24.04 -- hostname -I`) do set "WSLIP=%%i"
for /f "tokens=1" %%a in ("%WSLIP%") do set "WSLIP=%%a"
if "%WSLIP%"=="" (
  echo Failed to read the WSL IP address.
  exit /b 1
)
start "IM6 Virtual Board" wsl -d Ubuntu-24.04 -- bash -lc "cd /mnt/d/Workspace/StudyNote/IM6/qemu && IM6_BIND_HOST=0.0.0.0 IM6_ALLOWED_HOSTS=localhost:8765,127.0.0.1:8765,%WSLIP%:8765 IM6_IMAGE_DIR=/opt/im6/images python3 web/launch.py"
powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(45); do { try { $service=Invoke-RestMethod 'http://%WSLIP%:8765/version' -TimeoutSec 5; if ($service.service -eq 'im6-virtual-board') { Start-Process 'http://%WSLIP%:8765/'; exit 0 } } catch {}; Start-Sleep -Milliseconds 300 } while ((Get-Date) -lt $deadline); Write-Host 'Virtual board startup timed out. Check the service window.'; exit 1"
