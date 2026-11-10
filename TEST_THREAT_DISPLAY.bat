@echo off
cd /d "%~dp0"
set SPIDER_FIGHTS=1
set SPIDER_RETREAT_IDLE_SEC=130
set SPIDER_THREAT_SECONDS=3.5
py -3 spiderpet.pyw --duel
if errorlevel 1 pause
