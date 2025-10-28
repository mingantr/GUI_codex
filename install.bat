@echo off
setlocal
title Installation - Taolenn assistant PyQt5

REM Emplacement Python connu (selon nos échanges)
set "PYTHON_EXE=C:\Users\33679\AppData\Local\Programs\Python\Python39\python.exe"

if exist "%PYTHON_EXE%" (
  echo [INFO] Utilisation de "%PYTHON_EXE%"
) else (
  echo [WARN] Python 3.9 non trouvé a l'emplacement connu. On tente "python" depuis le PATH.
  set "PYTHON_EXE=python"
)

echo [INFO] Creation de l'environnement virtuel .venv ...
"%PYTHON_EXE%" -m venv .venv
if errorlevel 1 (
  echo [ERREUR] Echec de creation de l'environnement virtuel.
  pause
  exit /b 1
)

call .venv\Scripts\activate

echo [INFO] Mise a jour de pip ...
python -m pip install --upgrade pip

echo [INFO] Installation des dependances ...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERREUR] Echec d'installation des dependances.
  pause
  exit /b 1
)

if not exist ".env" (
  echo [INFO] Creation du fichier .env (depuis .env.example)
  copy .env.example .env >nul
  echo [ASTUCE] Ouvre le fichier .env et renseigne ta cle OPENAI_API_KEY.
)

echo [OK] Installation terminee.
pause
