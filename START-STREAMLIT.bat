@echo off
cd /d "%~dp0"
".venv312\Scripts\streamlit.exe" run app\streamlit_app.py
pause
