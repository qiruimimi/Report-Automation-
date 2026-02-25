#!/bin/bash
# 周报生成脚本
# 自动化运行，避免交互式输入问题

# 设置默认目标周（本周）
export CHOICE="1"

# 执行主程序
python3 main.py <<EOF
${CHOICE}
EOF
