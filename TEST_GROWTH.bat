@echo off
cd /d "%~dp0"
set SPIDER_RETREAT_IDLE_SEC=6
set SPIDER_DEN_REST_MIN_SEC=18
set SPIDER_DEN_REST_MAX_SEC=22
set SPIDER_NEST_GROW_DELAY_SEC=5
set SPIDER_NEST_GROW_SECONDS=18
set SPIDER_RETREAT_ABANDON_SEC=300
py -3 -m pip install Pillow
py -3 spiderpet.pyw
if errorlevel 1 pause
