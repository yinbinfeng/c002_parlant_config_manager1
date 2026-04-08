@echo off
echo ========================================
echo Creating new Python 3.11 environment
echo ========================================
call conda create -n py311_new python=3.11 -y

echo.
echo ========================================
echo Activating new environment and installing packages
echo ========================================
call conda activate py311_new
call conda install -n py311_new pip -y
call conda run -n py311_new pip install agentscope openai pyyaml json-repair python-dotenv loguru aiohttp pandas openpyxl tavily-python streamlit jsonschema mcp

echo.
echo ========================================
echo Verifying installation
echo ========================================
call conda run -n py311_new python -c "import agentscope; print('agentscope version:', agentscope.__version__)"

echo.
echo Done! Environment 'py311_new' is ready.
pause