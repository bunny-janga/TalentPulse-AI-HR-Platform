@echo off
TITLE TalentPulse AI Enterprise Platform
CLS
echo ===============================================================================
echo                TalentPulse AI Enterprise HR Management System
echo ===============================================================================
echo.
echo Choose how you want to run the project in VS Code:
echo.
echo [1] FastAPI Full Enterprise Stack (Backend Port 5000 / 8000 + React Frontend)
echo [2] Standalone Unified Flask Server (Port 8000 with Built-in Portal)
echo [3] Install All Python Dependencies First
echo [4] Run Automated Test Suite (Pytest 8 Phases)
echo.
set /p choice="Enter choice [1, 2, 3, or 4]: "

if "%choice%"=="1" goto run_fastapi
if "%choice%"=="2" goto run_flask
if "%choice%"=="3" goto install_deps
if "%choice%"=="4" goto run_tests

:run_fastapi
echo.
echo [*] Launching FastAPI Enterprise Stack on http://127.0.0.1:5000 (and :8000)...
cd backend
python -c "import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"
pause
exit

:run_flask
echo.
echo [*] Launching Unified Server on http://127.0.0.1:8000...
cd backend
python server.py
pause
exit

:install_deps
echo.
echo [*] Installing all dependencies from requirements.txt...
python -m pip install -r requirements.txt
echo [OK] Installation completed.
pause
exit

:run_tests
echo.
echo [*] Running 8-Phase Integration & Security Test Suite...
cd backend
pytest tests/ -v
pause
exit
