@echo off
cd /d "%~dp0"
py -3 -m pip install Pillow
if errorlevel 1 (pause & exit /b 1)
py -3 spiderpet.pyw
if errorlevel 1 pause
