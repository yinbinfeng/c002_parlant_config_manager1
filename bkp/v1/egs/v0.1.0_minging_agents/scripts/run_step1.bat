@echo off
REM prj/v0.4.0_complete/scripts/run_step1.bat
REM Run Step 1 only (Requirement Analysis)

echo ========================================
echo Mining Agents v0.4.0
echo Step 1: Requirement Analysis
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Get business description from argument or use default
set BUSINESS_DESC=%~1
if "%BUSINESS_DESC%"=="" (
    set BUSINESS_DESC=电商客服 Agent，处理订单查询、退换货和产品咨询
)

echo [INFO] Business Description: %BUSINESS_DESC%
echo [INFO] Step: 1 only
echo [INFO] Mode: Mock Mode
echo.

REM Run Step 1 only
python -m src.mining_agents.main ^
    --business-desc "%BUSINESS_DESC%" ^
    --config prj\v0.4.0_complete\config\system_config.yaml ^
    --start-step 1 ^
    --end-step 1 ^
    --mock-mode ^
    --verbose

if errorlevel 1 (
    echo.
    echo [ERROR] Execution failed. Please check the logs.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 1 Completed!
echo ========================================
echo.
echo Output file: output\step1\step1_clarification_questions.md
echo.

pause
