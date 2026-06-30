@echo off
setlocal

set "PROJECT_DIR=%~dp0"

echo ============================================================
echo  Bull Machines - Manual Production Order Management System
echo ============================================================
echo.

cd /d "%PROJECT_DIR%"

where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] uv is not installed. Get it from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo [INFO] Starting FastAPI server (dev) via uv...
echo [INFO] URL: http://localhost:8000
echo [INFO] API Docs: http://localhost:8000/docs
echo [INFO] Press Ctrl+C to stop.
echo.

call uv run run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server exited with code %ERRORLEVEL%.
    pause
)

endlocal
