@echo off
cd /d "%~dp0"
py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
echo.
echo Next: configure backend\.env, run backend\schema.sql in MySQL, then run python backend\app.py
pause
