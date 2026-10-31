@echo off
title Stop Miami Campus Server
echo ========================================================
echo  Stopping Miami Campus Central Server...
echo ========================================================
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    echo Stopping server process on port 5000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)
echo.
echo [✓] Miami Campus server stopped.
pause
