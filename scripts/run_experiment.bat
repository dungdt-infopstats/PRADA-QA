@echo off
REM MASEE Single Experiment Runner for Windows

echo ==========================================
echo   MASEE Experiment Runner (Windows)
echo ==========================================
echo.

REM Default parameters
set MODEL=gpt-4o-mini
set TYPE=base
set PART=100
set DATA=demo
set STEPS=3

REM Check for parameters
if not "%1"=="" set MODEL=%1
if not "%2"=="" set TYPE=%2
if not "%3"=="" set PART=%3
if not "%4"=="" set DATA=%4
if not "%5"=="" set STEPS=%5

echo [INFO] Experiment Parameters:
echo   Model: %MODEL%
echo   Type: %TYPE%
echo   Part: %PART%
echo   Data: %DATA%
echo   Steps: %STEPS%
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ and add to PATH
    pause
    exit /b 1
)

REM Create timestamp for logging
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

set LOG_FILE=%DATA%_log_%MODEL%_%TYPE%_%PART%_%timestamp%.txt

echo [INFO] Starting experiment...
echo [INFO] Log file: %LOG_FILE%
echo [INFO] Press Ctrl+C to cancel
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Run the experiment with logging (Windows doesn't have tee, so we'll redirect output)
python src/main.py %MODEL% %TYPE% %PART% %DATA% %STEPS% > %LOG_FILE% 2>&1

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Experiment completed successfully!
    echo ========================================
    echo [SUCCESS] Results saved to: %LOG_FILE%
) else (
    echo.
    echo ========================================
    echo   Experiment failed with errors
    echo ========================================
    echo [ERROR] Check log file: %LOG_FILE%
)

echo.
echo Press any key to exit...
pause >nul