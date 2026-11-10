@echo off
cd /d "%~dp0"
set SPIDER_RETREAT_IDLE_SEC=4
set SPIDER_DEN_REST_MIN_SEC=3
set SPIDER_DEN_REST_MAX_SEC=5
set SPIDER_FORAGE_MIN_SEC=15
set SPIDER_FORAGE_MAX_SEC=19
py -m pip install pillow
py spiderpet.pyw
pause
