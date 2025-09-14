@echo off
REM MASEE Test Suite Runner for Windows

echo ==========================================
echo   MASEE Test Suite (Windows)
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ and add to PATH
    pause
    exit /b 1
)

REM Check if pytest is installed
python -c "import pytest" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pytest not found! Installing...
    pip install pytest pytest-cov
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pytest
        pause
        exit /b 1
    )
)

echo [INFO] Running MASEE test suite...
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Run tests based on parameter
if "%1"=="unit" (
    echo [INFO] Running unit tests only...
    python -m pytest tests/unit/ -v
) else if "%1"=="integration" (
    echo [INFO] Running integration tests only...
    python -m pytest tests/integration/ -v
) else if "%1"=="performance" (
    echo [INFO] Running performance tests only...
    python -m pytest tests/performance/ -v
) else if "%1"=="coverage" (
    echo [INFO] Running all tests with coverage report...
    python -m pytest --cov=src --cov-report=html --cov-report=term -v
) else (
    echo [INFO] Running all tests...
    python -m pytest -v
)

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   All tests passed!
    echo ========================================
    echo [SUCCESS] Your MASEE system is working correctly
) else (
    echo.
    echo ========================================
    echo   Some tests failed
    echo ========================================
    echo [WARNING] Check the output above for details
    echo [INFO] Common issues: missing dependencies or configuration
)

echo.
echo Press any key to exit...
pause >nul