@echo off
setlocal
cd /d "%~dp0"

rem Ensure local src is importable without hard-coded paths
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

rem Prefer local venv if it exists
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" -m app

