@echo off
cd /d "%~dp0"
if exist "dist\SpiderPet.exe" (
  start "" "dist\SpiderPet.exe" --duel
  exit /b 0
)
py -3 -m pip install Pillow
if errorlevel 1 (pause & exit /b 1)
py -3 spiderpet.pyw --duel
if errorlevel 1 pause
