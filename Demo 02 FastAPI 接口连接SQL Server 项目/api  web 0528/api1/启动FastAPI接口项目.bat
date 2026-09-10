@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   FastAPI 接口服务 - 一键启动
echo ============================================
echo [1/3] 检查依赖包...
python -c "import fastapi, uvicorn, pyodbc, pydantic" >nul 2>&1
if errorlevel 1 (
    echo 依赖检查失败，请先执行: pip install -r requirements.txt
    pause
    exit /b 1
)
echo 依赖检查通过。
echo [2/3] 测试数据库连接...
python -c "from database import get_db_connection; get_db_connection(); print('ok')" >nul 2>&1
if errorlevel 1 (
    echo 数据库连接失败，请确认 SQL Server 服务已启动、数据库名称正确。
    pause
    exit /b 1
)
echo 数据库连接成功。
echo [3/3] 正在启动 FastAPI 服务...
echo 接口地址：http://127.0.0.1:9001
echo 接口文档：http://127.0.0.1:9001/docs
echo 停止方式：关闭本窗口，或运行 关闭FastAPI接口项目.bat
echo ============================================
python main.py
pause
