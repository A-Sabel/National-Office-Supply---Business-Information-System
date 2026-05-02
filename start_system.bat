@echo off
SETLOCAL EnableDelayedExpansion

echo   National Office Supplies - System Initializer

:: 1. Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: 2. Create Virtual Environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating Virtual Environment (venv)...
    python -m venv venv
)

:: 3. Activate and Install Dependencies
echo [INFO] Activating environment and verifying libraries...
call venv\Scripts\activate

:: Use the requirements file to ensure CustomTkinter is installed
pip install -r dev-requirements.txt

:: 4. Launch the Application
echo [INFO] Launching Management System...
:: Navigating into the nested structure to find the source
python "national_office_supply_BIS_project/national_office_supply_BIS/src/__main__.py"

if %errorlevel% neq 0 (
    echo.
    echo [SYSTEM] Application closed with an error.
    pause
)

deactivate
echo [INFO] Session closed.