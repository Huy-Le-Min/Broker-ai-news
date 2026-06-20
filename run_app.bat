@echo off
title Vietcap Hub
cd /d E:\Automation
echo Kiem tra dependencies...
py -m pip install -q fastapi "uvicorn[standard]" jinja2 aiofiles
echo.
echo ========================================
echo  Vietcap Hub dang chay tai:
echo  http://localhost:8080
echo  Nhan Ctrl+C de dung server.
echo ========================================
echo.
py -m uvicorn app.main:app --host 127.0.0.1 --port 8080
pause
