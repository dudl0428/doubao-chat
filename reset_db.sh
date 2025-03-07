#!/bin/bash

echo "=== 豆包AI聊天应用数据库重置脚本 ==="
echo "警告: 此操作将删除所有数据库数据！"
read -p "是否继续? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "操作已取消"
    exit 0
fi

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "错误: 未找到虚拟环境，请先运行 ./install.sh"
    exit 1
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 设置环境变量
export FLASK_APP=run.py
export FLASK_ENV=development

# 删除数据库文件
echo "正在删除数据库文件..."
rm -f instance/app.db
rm -rf migrations

# 重新初始化数据库
echo "正在重新初始化数据库..."
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo "=== 数据库重置完成 ===" 