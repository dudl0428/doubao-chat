@echo off
echo === 豆包AI聊天应用安装脚本 ===
echo 正在设置环境...

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请先安装Python
    exit /b 1
)

REM 创建虚拟环境
echo 正在创建虚拟环境...
python -m venv venv

REM 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

REM 使用清华大学镜像源安装依赖
echo 正在使用清华大学镜像源安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 创建.env文件（如果不存在）
if not exist .env (
    echo 正在创建.env文件...
    copy .env.example .env
    echo 请编辑.env文件，设置您的SECRET_KEY和OPENAI_API_KEY
)

REM 设置环境变量
set FLASK_APP=run.py
set FLASK_ENV=development

REM 初始化数据库
echo 正在初始化数据库...
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo === 安装完成 ===
echo 请运行以下命令启动应用:
echo venv\Scripts\activate
echo start.bat

pause 