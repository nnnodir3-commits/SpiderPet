@echo off
setlocal
cd /d "%~dp0"
title SpiderPet v36 - DEBUG BUILD
echo Building DEBUG EXE with visible console...
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher [py] is unavailable.
  goto :FAIL
)
py -3 -m pip install Pillow PyInstaller
if errorlevel 1 goto :FAIL
py -3 -m PyInstaller --clean --noconfirm --onefile --console --name SpiderPet_DEBUG --add-data "walk_*.png;." --add-data "threat_*.png;." spiderpet.pyw
if errorlevel 1 goto :FAIL
if not exist "dist\SpiderPet_DEBUG.exe" goto :FAIL
echo DEBUG EXE built: dist\SpiderPet_DEBUG.exe
 echo When it fails, read the error in this window.
"dist\SpiderPet_DEBUG.exe"
echo.
echo DEBUG PROGRAM EXITED. Exit code: %errorlevel%
pause
exit /b 0
:FAIL
echo DEBUG BUILD FAILED.
pause
exit /b 1
