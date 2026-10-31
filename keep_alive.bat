@echo off
title Miami Campus 24/7 Watchdog Server (خادم مستمر 24 ساعة)
echo ========================================================
echo  Miami Campus - 24/7 Auto-Restart Watchdog
echo  If the server stops, it will restart automatically!
echo ========================================================
:loop
echo [%date% %time%] Starting server...
python server.py
echo.
echo [%date% %time%] WARNING: Server exited. Auto-restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
