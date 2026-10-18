@echo off
setlocal
set "FMM_PREVIEW_PY=%~dp0.venv\Scripts\pythonw.exe"
if not exist "%FMM_PREVIEW_PY%" goto missing
start "" "%FMM_PREVIEW_PY%" "%~dp0scripts\preview_event.py"
exit /b 0
:missing
echo Project environment is missing. Run setup.bat first.
pause
exit /b 1
