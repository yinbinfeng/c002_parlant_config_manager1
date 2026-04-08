@echo off
REM prj/v0.4.0_complete/scripts/run_all_steps.bat
REM Run all 8 steps of Mining Agents

echo ========================================
echo Mining Agents v0.4.0 - Complete
echo Running All 8 Steps
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
echo [INFO] Steps: 1 to 8 (Complete Workflow)
echo [INFO] Mode: Mock Mode (for testing)
echo.

REM Run all 8 steps
python -m src.mining_agents.main ^
    --business-desc "%BUSINESS_DESC%" ^
    --config prj\v0.4.0_complete\config\system_config.yaml ^
    --start-step 1 ^
    --end-step 8 ^
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
echo Execution Completed Successfully!
echo ========================================
echo.
echo Output files are located in: output/
echo   - step1/: Clarification questions
echo   - step2/: Multi-agent debate results
echo   - step3/: Task breakdown
echo   - step4/: Global rules
echo   - step5/: Domain configuration
echo   - step6/: User portrait analysis
echo   - step7/: Quality report
echo   - step8/: Final Parlant configuration
echo.

pause
