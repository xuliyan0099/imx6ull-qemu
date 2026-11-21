@echo off
start "IM6 Virtual Board GTK" wsl -d Ubuntu-24.04 -- bash -lc "cd /mnt/d/Workspace/StudyNote/IM6/qemu && IM6_DISPLAY=gtk python3 web/launch.py"
powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(30); do { try { $service=Invoke-RestMethod 'http://127.0.0.1:8765/version' -TimeoutSec 5; if ($service.service -eq 'im6-virtual-board') { Start-Process 'http://localhost:8765/'; exit 0 } } catch {}; Start-Sleep -Milliseconds 300 } while ((Get-Date) -lt $deadline); Write-Host 'Virtual board startup timed out. Check the service window.'; exit 1"
