@echo off
setlocal
set "LOG=%LOCALAPPDATA%\SpiderPet\spiderpet_error.log"
if exist "%LOG%" (
  notepad "%LOG%"
) else (
  echo Error log not found: %LOG%
  echo Run TEST_EXE.bat first.
  pause
)
