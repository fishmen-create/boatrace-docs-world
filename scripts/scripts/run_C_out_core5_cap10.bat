@echo off
setlocal
set DATE=%1
if "%DATE%"=="" (
  echo Usage: %~nx0 YYYY-MM-DD
  exit /b 1
)
set SCRIPT_DIR=%~dp0
set WORK_DIR=%SCRIPT_DIR%..
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_C_out_core5_cap10.ps1" -Date "%DATE%" -WorkDir "%WORK_DIR%"
