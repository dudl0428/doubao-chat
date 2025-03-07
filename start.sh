#!/bin/bash

echo "=== 豆包AI聊天应用启动脚本 ==="

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "错误: 未找到虚拟环境，请先运行 ./install.sh"
    exit 1
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "警告: 未找到.env文件，正在创建..."
    cp .env.example .env
    echo "请编辑.env文件，设置您的SECRET_KEY和OPENAI_API_KEY"
fi

# 设置环境变量
export FLASK_APP=run.py
export FLASK_ENV=development

# 运行应用
echo "正在启动应用..."
flask run

# 如果应用异常退出，保持终端窗口打开
echo "应用已停止运行。按任意键退出..."
read -n 1 