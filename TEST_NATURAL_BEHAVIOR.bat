@echo off
cd /d "%~dp0"
set SPIDER_FIGHTS=0
set SPIDER_IDLE_ACTION_SEC=3
set SPIDER_RETREAT_IDLE_SEC=90
py -3 spiderpet.pyw
if errorlevel 1 pause
