@echo off
echo Starting Nutrimind Project...

:: Set the API key for this session
set OPENAI_API_KEY=AIzaSyCVRVBXQ_lk5ze4fb1y71Sy_JdeOhn_WhY

:: Start the FastAPI Backend in a new command prompt window
echo Starting Backend...
start "Nutrimind Backend" cmd /k "cd FastAPI_Backend && ..\venv\Scripts\python -m uvicorn main:app --reload --port 8080"

:: Start the React Frontend in a new command prompt window
echo Starting Frontend...
start "Nutrimind Frontend" cmd /k "cd react_frontend && npm run dev"

echo.
echo Both services are starting up in separate windows!
echo - The backend will be available at http://localhost:8080
echo - The frontend will be available at http://localhost:5173 (or 5174 if 5173 is in use)
echo.
echo You can close this window now. The servers will continue running in the newly opened windows.
pause
