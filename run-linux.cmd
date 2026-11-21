@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run-linux.ps1" %*
