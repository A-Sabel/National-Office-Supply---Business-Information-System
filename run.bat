@echo off
echo [INFO] Starting National Office Supplies System...

:: Navigate to the directory of the batch file
cd /d "%~dp0"

:: Activate the environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    pause
    exit
)

:: Run using the relative path (with quotes to handle spaces)
python "national_office_supply_BIS_project/national_office_supply_BIS/src/__main__.py"

pause