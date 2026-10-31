@echo off
title Install Miami Campus 24/7 Auto-Start
echo ========================================================
echo  Configuring Miami Campus Server to Auto-Start on Boot...
echo ========================================================

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_SCRIPT=%~dp0run_background.vbs"

echo Creating startup shortcut in:
echo %STARTUP_FOLDER%

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_FOLDER%\MiamiCampusServer.lnk'); $s.TargetPath = '%VBS_SCRIPT%'; $s.WorkingDirectory = '%~dp0'; $s.Save()"

if exist "%STARTUP_FOLDER%\MiamiCampusServer.lnk" (
    echo.
    echo [✓] SUCCESS! Miami Campus server will now start automatically
    echo     in the background every time this computer turns on.
) else (
    echo [✗] Could not create shortcut. Please copy run_background.vbs to shell:startup manually.
)

echo.
pause
