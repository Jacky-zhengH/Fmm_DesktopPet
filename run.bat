@echo off
setlocal
set "FMM_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%FMM_PY%" goto missing
"%FMM_PY%" -c "import PySide6.QtWidgets" >nul 2>&1
if errorlevel 1 goto missing
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app\main.py" %*
exit /b 0
:missing
echo Project environment is missing or incomplete. Run setup.bat first.
pause
exit /b 1
