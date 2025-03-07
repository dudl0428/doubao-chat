@echo off
echo === 豆包AI聊天应用数据库重置脚本 ===
echo 警告: 此操作将删除所有数据库数据！

set /p confirm=是否继续? (y/n): 
if /i not "%confirm%"=="y" (
    echo 操作已取消
    exit /b 0
)

REM 检查虚拟环境是否存在
if not exist venv (
    echo 错误: 未找到虚拟环境，请先运行 install.bat
    exit /b 1
)

REM 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

REM 设置环境变量
set FLASK_APP=run.py
set FLASK_ENV=development

REM 删除数据库文件
echo 正在删除数据库文件...
if exist instance\app.db del /f instance\app.db
if exist migrations rmdir /s /q migrations

REM 重新初始化数据库
echo 正在重新初始化数据库...
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo === 数据库重置完成 ===
pause 