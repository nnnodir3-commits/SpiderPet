@echo off
setlocal
cd /d "%~dp0"
title SpiderPet v38 - ONE EXE BUILDER
echo ============================================
echo  SpiderPet v38 - Build single Windows EXE
 echo ============================================
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python Launcher [py] not found.
  echo Install Python 3.10+ from python.org, then retry.
  goto :FAIL
)
py -3 --version
if errorlevel 1 goto :FAIL
 echo Installing/checking build tools...
py -3 -m pip install --upgrade Pillow PyInstaller
if errorlevel 1 goto :FAIL
 echo.
 echo Building dist\SpiderPet.exe ...
py -3 -m PyInstaller --clean --noconfirm --onefile --windowed --name SpiderPet --add-data "walk_*.png;." --add-data "threat_*.png;." spiderpet.pyw
if errorlevel 1 goto :FAIL
if not exist "dist\SpiderPet.exe" (
  echo ERROR: dist\SpiderPet.exe was not created.
  goto :FAIL
)
echo.
echo BUILD OK: "%CD%\dist\SpiderPet.exe"
echo Run TEST_EXE.bat to test with error reporting.
pause
exit /b 0
:FAIL
echo.
echo BUILD FAILED. Copy or photograph the error text above.
pause
exit /b 1
