@echo off
cd /d "%~dp0"
py -m pip install pillow pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name SpiderPet --add-data "walk_*.png;." --add-data "threat_*.png;." spiderpet.pyw
pause
