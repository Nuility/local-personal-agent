@echo off
wsl -d Ubuntu-24.04 --cd "%~dp0." -- bash start.sh
pause
