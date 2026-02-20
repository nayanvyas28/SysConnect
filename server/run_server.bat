@echo off
cd %~dp0
venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
