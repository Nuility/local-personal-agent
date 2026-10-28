@echo off
wsl -d Ubuntu-24.04 --cd "%~dp0." -- python3 stop.py
pause
