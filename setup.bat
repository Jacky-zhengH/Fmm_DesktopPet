@echo off
setlocal
pushd "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 goto fallback
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:fallback
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 goto python_missing
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r "requirements\base.txt"
if errorlevel 1 goto failed
echo Ready. Double-click run.bat to launch the source build.
popd
pause
exit /b 0
:python_missing
echo Python 3.10 or newer is required. Install Python, then run setup.bat again.
goto failed
:failed
echo Setup failed. Check the message above.
popd
pause
exit /b 1
