@echo off
setlocal
cd /d "%~dp0"
title SpiderPet v29 - EXE TEST
echo SpiderPet EXE diagnostics.
if not exist "dist\SpiderPet.exe" (
  echo ERROR: dist\SpiderPet.exe not found.
  echo Run BUILD_ONE_EXE.bat first.
  pause
  exit /b 1
)
echo The program is starting. This window remains open until it exits.
echo If no spider appears, please check the error log below.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Start-Process -FilePath '.\dist\SpiderPet.exe' -WorkingDirectory (Get-Location).Path -Wait -PassThru; Write-Host ('Process exit code: ' + $p.ExitCode)"
echo.
echo Error log: %LOCALAPPDATA%\SpiderPet\spiderpet_error.log
if exist "%LOCALAPPDATA%\SpiderPet\spiderpet_error.log" (
  echo ================== ERROR LOG ==================
  type "%LOCALAPPDATA%\SpiderPet\spiderpet_error.log"
) else (
  echo No error log file was produced.
  echo If no spider appeared, run BUILD_DEBUG_EXE.bat next.
)
echo.
pause
