@echo off
title ToolListen - Live Subtitle & Translator
chcp 65001 >nul
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Co van de khi khoi chay. Nhan phim bat ky de thoat...
    pause >nul
)
