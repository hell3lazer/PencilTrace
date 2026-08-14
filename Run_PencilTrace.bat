@echo off
title PencilTrace Server
echo Starting PencilTrace Server...
echo Please leave this window open while using the application.
echo.
cd /d "%~dp0"
python backend\app.py
pause
