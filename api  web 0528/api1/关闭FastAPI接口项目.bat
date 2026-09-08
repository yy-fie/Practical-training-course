@echo off
chcp 65001 >nul
echo ============================================
echo   FastAPI 接口服务 - 一键停止
echo ============================================
echo 正在停止 FastAPI 接口服务（端口 9001）...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":9001" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
echo 接口服务已停止。
pause
