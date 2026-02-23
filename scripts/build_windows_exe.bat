@echo off
setlocal

if "%VIRTUAL_ENV%"=="" (
  echo [INFO] No virtualenv detected. It is recommended to activate one first.
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --clean --windowed --name BlueOceanEarningsWatch app/main.py

if %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Build failed.
  exit /b %ERRORLEVEL%
)

echo [DONE] EXE generated at dist\BlueOceanEarningsWatch\BlueOceanEarningsWatch.exe
