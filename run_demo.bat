@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=D:\Study\venv-nckh\Scripts\python.exe
if not exist "%PY%" set PY=python
echo Dang khoi dong LabSafe... trinh duyet se tu mo tai http://localhost:8501
"%PY%" -m streamlit run app\main.py
pause
