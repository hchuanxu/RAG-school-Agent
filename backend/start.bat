@echo off
REM 校园多源知识库智能问答助手 - 后端启动脚本
REM 使用 campus 虚拟环境运行

cd /d d:\Campus_Assistant\backend

REM 设置环境变量
set PYTHONPATH=d:\Campus_Assistant\backend;d:\Campus_Assistant\backend\libs

REM 使用 campus 环境的 Python 启动
D:\anaconda3\envs\campus\python.exe run.py

pause
