@echo off
REM MASEE Demo Runner for Windows
REM Quick test of the complete MASEE workflow

echo ==========================================
echo   MASEE Full Workflow Demo (Windows)
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ and add to PATH
    pause
    exit /b 1
)

echo [INFO] Running MASEE demonstration...
echo [INFO] This will test all 6 workflow steps
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Run the demo
python run_demo.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Demo completed successfully!
    echo ========================================
    echo [SUCCESS] Your MASEE system is ready!
    echo [INFO] Check demo_experiment_results.json for sample output
) else (
    echo.
    echo ========================================
    echo   Demo failed with errors
    echo ========================================
    echo [ERROR] Please check the error messages above
    echo [INFO] Common issues: missing dependencies, API keys, or config files
)

echo.
echo Press any key to exit...
pause >nul