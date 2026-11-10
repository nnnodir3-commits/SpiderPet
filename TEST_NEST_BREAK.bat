@echo off
cd /d "%~dp0"
set SPIDER_RETREAT_IDLE_SEC=3
set SPIDER_DEN_REST_MIN_SEC=8
set SPIDER_DEN_REST_MAX_SEC=10
py -m pip install pillow
py spiderpet.pyw
pause
