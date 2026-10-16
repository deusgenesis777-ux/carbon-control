@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=G:\PY\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Python not found at %PYTHON_EXE%.
  echo Install Python or update PYTHON_EXE in setup.bat.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  "%PYTHON_EXE%" -m venv .venv
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo Setup complete. Use run.bat for normal launches.
pause
exit /b 0
:error
echo Setup failed. Check the error above.
pause
exit /b 1
endlocal
