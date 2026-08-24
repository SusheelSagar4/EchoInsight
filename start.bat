@echo off
REM =========================================================================
REM EchoInsight Startup Script
REM
REM This batch file launches the EchoInsight development environment in two
REM separate command prompt windows:
REM
REM 1. Backend Server:
REM    - Navigates to the project root (C:\Bunty\IIT BBS\PM\EchoInsight)
REM    - Activates the virtual environment (venv)
REM    - Moves into the backend folder (C:\Bunty\IIT BBS\PM\EchoInsight\backend)
REM    - Runs: uvicorn app.main:app --reload
REM
REM 2. Frontend Server:
REM    - Navigates directly to the frontend folder (C:\Bunty\IIT BBS\PM\EchoInsight\frontend)
REM    - Runs: npm run dev
REM =========================================================================

REM Launch Backend Development Server
start "EchoInsight Backend" cmd /k "cd /d "C:\Bunty\IIT BBS\PM\EchoInsight" && call "C:\Bunty\IIT BBS\PM\EchoInsight\venv\Scripts\activate.bat" && cd /d "C:\Bunty\IIT BBS\PM\EchoInsight\backend" && uvicorn app.main:app --reload"

REM Launch Frontend Development Server
start "EchoInsight Frontend" cmd /k "cd /d "C:\Bunty\IIT BBS\PM\EchoInsight\frontend" && npm run dev"
