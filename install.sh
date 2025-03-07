#!/bin/bash

echo "=== 豆包AI聊天应用安装脚本 ==="
echo "正在设置环境..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 创建虚拟环境
echo "正在创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 使用清华大学镜像源安装依赖
echo "正在使用清华大学镜像源安装依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建.env文件（如果不存在）
if [ ! -f .env ]; then
    echo "正在创建.env文件..."
    cp .env.example .env
    echo "请编辑.env文件，设置您的SECRET_KEY和OPENAI_API_KEY"
fi

# 设置环境变量
export FLASK_APP=run.py
export FLASK_ENV=development

# 初始化数据库
echo "正在初始化数据库..."
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo "=== 安装完成 ==="
echo "请运行以下命令启动应用:"
echo "source venv/bin/activate"
echo "./start.sh" 