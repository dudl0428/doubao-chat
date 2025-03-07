@echo off
echo === 豆包AI聊天应用启动脚本 ===

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

REM 运行应用
echo 正在启动应用...
flask run

pause 