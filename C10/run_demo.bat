@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === C10 第二大脑 · 演示 ===
python agent.py --demo
echo.
echo === 契约测试 ===
python tests/test_smoke.py
