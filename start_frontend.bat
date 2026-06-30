@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"

echo ============================================================
echo  Bull Machines - Manual Production Order UI (Vite / React)
echo ============================================================
echo.

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [INFO] node_modules not found. Installing dependencies...
    cd /d "%FRONTEND_DIR%"
    npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
)

cd /d "%FRONTEND_DIR%"

echo [INFO] Starting Vite dev server...
echo [INFO] URL: http://localhost:3000
echo [INFO] API proxy: http://localhost:8000
echo [INFO] Press Ctrl+C to stop.
echo.

npm run dev -- --host

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Vite dev server exited with code %ERRORLEVEL%.
    pause
)

endlocal
