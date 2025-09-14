@echo off
setlocal enabledelayedexpansion
REM MASEE Batch Experiment Runner for Windows

echo ==========================================
echo   MASEE Batch Experiments (Windows)
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ and add to PATH
    pause
    exit /b 1
)

REM Batch experiment configurations
set MODELS=gpt-4o-mini
set TYPES=base base-description
set PARTS=50 100
set DATA_CHOICES=demo
set STEPS=3

echo [INFO] Batch Experiment Configuration:
echo   Models: %MODELS%
echo   Types: %TYPES%
echo   Parts: %PARTS%
echo   Data: %DATA_CHOICES%
echo   Steps: %STEPS%
echo.
echo [INFO] This will run multiple experiments sequentially
echo [WARNING] This may take a while depending on your configuration
echo.

set /p CONFIRM="Continue with batch experiments? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo [INFO] Batch experiments cancelled
    pause
    exit /b 0
)

echo.
echo [INFO] Starting batch experiments...
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Counter for experiments
set COUNT=0

REM Loop through configurations
for %%m in (%MODELS%) do (
    for %%t in (%TYPES%) do (
        for %%p in (%PARTS%) do (
            for %%d in (%DATA_CHOICES%) do (
                set /a COUNT+=1
                echo ==========================================
                echo   Experiment !COUNT!: %%m %%t %%p %%d %STEPS%
                echo ==========================================

                REM Create timestamp for logging
                for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
                set "YY=!dt:~2,2!" & set "YYYY=!dt:~0,4!" & set "MM=!dt:~4,2!" & set "DD=!dt:~6,2!"
                set "HH=!dt:~8,2!" & set "Min=!dt:~10,2!" & set "Sec=!dt:~12,2!"
                set "timestamp=!YYYY!-!MM!-!DD!_!HH!-!Min!-!Sec!"

                set "LOG_FILE=%%d_log_%%m_%%t_%%p_!timestamp!.txt"

                echo [INFO] Running: %%m %%t %%p %%d %STEPS%
                echo [INFO] Log: !LOG_FILE!

                python src/main.py %%m %%t %%p %%d %STEPS% > "!LOG_FILE!" 2>&1

                if !errorlevel! equ 0 (
                    echo [SUCCESS] Experiment !COUNT! completed
                ) else (
                    echo [ERROR] Experiment !COUNT! failed - check !LOG_FILE!
                )
                echo.
            )
        )
    )
)

echo ==========================================
echo   Batch Experiments Complete
echo ==========================================
echo [INFO] Completed %COUNT% experiments
echo [INFO] Check individual log files for results
echo.

echo Press any key to exit...
pause >nul