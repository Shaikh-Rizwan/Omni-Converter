@echo off
title OmniConvert Video Converter
cd /d "%~dp0"

set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if exist "%PYTHON_PATH%" (
    start "" "%PYTHON_PATH%" main.py
    exit /b 0
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    start "" python main.py
    exit /b 0
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    start "" py -3 main.py
    exit /b 0
)

echo [ERROR] Python 3 was not found. Please verify Python is installed.
pause
exit /b 1

