@echo off
cd /d "%~dp0"
py -3 main.py
if errorlevel 1 (
    echo.
    echo Could not start. Install Python 3 with Tkinter, then run main.py using IDLE.
    pause
)
