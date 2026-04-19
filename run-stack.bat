@echo off
set SCRIPT_DIR=%~dp0

powershell ^
  -NoProfile ^
  -ExecutionPolicy Bypass ^
  -File "%SCRIPT_DIR%docker-compose-run.ps1" ^
  -BackendPath  "C:\Users\User\Documents\bojan_project\backend"

pause
