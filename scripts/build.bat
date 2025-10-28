@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0\.."

rem Prefer local venv python
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

rem App name
set "NAME=PyQtTemplate"

rem Ensure PyInstaller is available
"%PY%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] PyInstaller n'est pas installe dans cet environnement.
  echo         Installez-le : %PY% -m pip install pyinstaller
  exit /b 1
)

echo [INFO] Build %NAME% avec PyInstaller...
"%PY%" -m PyInstaller -n %NAME% --noconfirm --clean ^
  -p src ^
  --add-data "assets;assets" ^
  src\app\__main__.py

if errorlevel 1 (
  echo [ERREUR] Echec du build.
  exit /b 1
)

echo [OK] Build termine. Binaire: dist\%NAME%\%NAME%.exe
exit /b 0

