@echo off
echo Setting up National Office Supplies System...

:: 1. Create venv if it doesn't exist
if not exist "venv" (
    echo Creating Virtual Environment...
    python -m venv venv
)

:: 2. Activate and Install
echo Installing/Verifying Dependencies...
call venv\Scripts\activate
pip install -r dev-requirements.txt

:: 3. Run the App
echo Launching System...
python national_office_supply_BIS_project/national_office_supply_BIS/src/__main__.py

pause