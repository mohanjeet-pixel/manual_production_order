@echo off
setlocal
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo ============================================================
echo  Bull Machines - Manual Production Order  (local deploy)
echo ============================================================
echo.

where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] uv is not installed. Get it from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

if not exist ".env" (
    echo [WARN] .env not found - creating one from .env.example.
    copy ".env.example" ".env" >nul
    echo [WARN] Edit .env with real credentials, then run start.bat again.
    pause
    exit /b 1
)

echo [1/4] Syncing Python dependencies with uv...
call uv sync
if %ERRORLEVEL% NEQ 0 ( echo [ERROR] uv sync failed. & pause & exit /b 1 )

echo [2/4] Setting up database (create if missing + apply migrations)...
call uv run python -m backend.scripts.init_db
if %ERRORLEVEL% NEQ 0 ( echo [ERROR] database setup failed - is PostgreSQL running and .env correct? & pause & exit /b 1 )

echo [3/4] Building frontend...
pushd frontend
if not exist "node_modules" (
    call npm install
    if %ERRORLEVEL% NEQ 0 ( echo [ERROR] npm install failed. & popd & pause & exit /b 1 )
)
call npm run build
if %ERRORLEVEL% NEQ 0 ( echo [ERROR] frontend build failed. & popd & pause & exit /b 1 )
popd

echo.
echo [4/4] Starting application...
echo       App:      http://localhost:8000
echo       API docs: http://localhost:8000/docs
echo       Press Ctrl+C to stop.
echo.
call uv run run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with code %ERRORLEVEL%.
    pause
)
endlocal
