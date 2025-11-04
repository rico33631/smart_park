@echo off
REM Smart Parking System - Quick Start Script for Windows

echo ======================================
echo Smart Parking System - Quick Start
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Check if database exists
if not exist "parking.db" (
    echo.
    echo Database not found. Generating sample data...
    python generate_sample_data.py
)

REM Start the application
echo.
echo ======================================
echo Starting Smart Parking System...
echo ======================================
echo Dashboard: http://localhost:5000
echo Press Ctrl+C to stop
echo ======================================
echo.

python app.py
