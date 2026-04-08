@echo off
echo 正在启动会话流程规则挖掘系统 UI (Mock 模式)...
echo.
echo 使用说明:
echo - 该脚本将启动 Streamlit UI 在 Mock 模式下
echo - Mock 模式不会调用真实 LLM，仅用于 UI 测试
echo.
python -m streamlit run egs\v0.1.0_minging_agents\run_ui.py -- --mock
