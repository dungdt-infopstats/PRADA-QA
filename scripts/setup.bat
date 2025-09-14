@echo off
REM MASEE Environment Setup for Windows

echo ==========================================
echo   MASEE Environment Setup (Windows)
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo [INFO] Please install Python 3.10+ from https://python.org
    echo [INFO] Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found! Please reinstall Python with pip included
    pause
    exit /b 1
)

echo [INFO] pip found:
pip --version
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Install dependencies
echo [INFO] Installing Python dependencies...
echo [INFO] This may take a few minutes...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo [INFO] Try running: pip install --user -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Dependencies installed successfully!
echo.

REM Check if .env file exists
if not exist .env (
    echo [INFO] Creating .env file template...
    echo # MASEE Environment Configuration > .env
    echo # Copy this to .env and add your API keys >> .env
    echo. >> .env
    echo # OpenAI API Key >> .env
    echo OPENAI_API_KEY=your_openai_api_key_here >> .env
    echo. >> .env
    echo # Tavily API Key for web search >> .env
    echo TAVILY_API_KEY=your_tavily_api_key_here >> .env
    echo. >> .env
    echo # Other API keys as needed >> .env
    echo ANTHROPIC_API_KEY=your_anthropic_api_key_here >> .env

    echo [INFO] Created .env template file
    echo [IMPORTANT] Edit .env file with your actual API keys before running experiments
) else (
    echo [INFO] .env file already exists
)

echo.

REM Verify installation by running a quick test
echo [INFO] Testing installation...
echo.

python -c "import sys; import pandas; import yaml; import smolagents; print('[SUCCESS] All core dependencies working')" 2>nul

if %errorlevel% equ 0 (
    echo [SUCCESS] Installation verification passed!
    echo.
    echo ==========================================
    echo   Setup Complete! Next Steps:
    echo ==========================================
    echo 1. Edit .env file with your API keys
    echo 2. Run: run_demo.bat
    echo 3. If demo works, try: run_experiment.bat
    echo 4. For batch processing: run_batch.bat
    echo 5. To run tests: run_tests.bat
    echo.
) else (
    echo [WARNING] Some dependencies may not be working correctly
    echo [INFO] Try running run_demo.bat to see if everything works
    echo.
)

echo Press any key to exit...
pause >nul