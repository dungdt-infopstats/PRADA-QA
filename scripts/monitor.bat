@echo off
REM MASEE Monitoring and Status Checker for Windows

echo ==========================================
echo   MASEE System Monitor (Windows)
echo ==========================================
echo.

REM Check parameter for action
set ACTION=%1
if "%ACTION%"=="" set ACTION=status

if /i "%ACTION%"=="status" goto :status
if /i "%ACTION%"=="logs" goto :logs
if /i "%ACTION%"=="processes" goto :processes
if /i "%ACTION%"=="files" goto :files
if /i "%ACTION%"=="help" goto :help

:status
echo [INFO] System Status Check
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python:
    python --version
) else (
    echo [ERROR] Python not found
)

REM Check dependencies
python -c "import pandas, yaml, smolagents" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Core dependencies installed
) else (
    echo [WARNING] Some dependencies missing
)

REM Check .env file
if exist .env (
    echo [OK] Environment file (.env) exists
) else (
    echo [WARNING] .env file missing - create with setup.bat
)

REM Check config files
if exist "config\meta_agent.yaml" (
    echo [OK] Agent configuration found
) else (
    echo [WARNING] Agent configuration missing
)

REM Check data files
if exist "data\demo_pqa_validation_part100.csv" (
    echo [OK] Demo data files found
) else (
    echo [WARNING] Demo data files missing
)

REM Check for custom smolagents
if exist "masee\Lib\site-packages\smolagents" (
    echo [OK] Custom smolagents environment found
) else (
    echo [WARNING] Custom smolagents not found
)

echo.
goto :end

:logs
echo [INFO] Recent Log Files
echo.
dir *_log_*.txt /B /O:D 2>nul | findstr . && (
    echo.
    echo [INFO] Use 'type filename.txt' to view log content
) || (
    echo [INFO] No log files found
)
echo.
goto :end

:processes
echo [INFO] Python Processes Running
echo.
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE 2>nul | findstr python.exe && (
    echo.
    echo [INFO] Python processes are running
    echo [INFO] These might be MASEE experiments
) || (
    echo [INFO] No Python processes found
)
echo.
goto :end

:files
echo [INFO] Project Structure Overview
echo.

REM Change to project root directory
cd /d "%~dp0.."

echo Main directories:
for /d %%i in (*) do (
    if /i not "%%i"=="legacy" (
        if /i not "%%i"=="archive" (
            if /i not "%%i"=="__pycache__" (
                echo   [DIR] %%i\
            )
        )
    )
)
echo.
echo Key files:
if exist run_demo.py echo   [FILE] run_demo.py - Full workflow demo
if exist run_demo.bat echo   [FILE] run_demo.bat - Windows demo runner
if exist README.md echo   [FILE] README.md - Documentation
if exist requirements.txt echo   [FILE] requirements.txt - Dependencies
if exist .env echo   [FILE] .env - Environment configuration
echo.
goto :end

:help
echo MASEE Monitor - Usage:
echo.
echo   monitor.bat [action]
echo.
echo Actions:
echo   status      - Check system status (default)
echo   logs        - Show recent log files
echo   processes   - Show running Python processes
echo   files       - Show project structure
echo   help        - Show this help
echo.
echo Examples:
echo   monitor.bat
echo   monitor.bat status
echo   monitor.bat logs
echo.
goto :end

:end
if not "%1"=="help" (
    echo Press any key to exit...
    pause >nul
)