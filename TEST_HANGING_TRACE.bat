@echo off
cd /d "%~dp0"
set SPIDER_HANG_TRACE=1
call TEST_HANGING.bat
