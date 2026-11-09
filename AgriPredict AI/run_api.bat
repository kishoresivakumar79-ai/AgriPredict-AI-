@echo off
echo ========================================================
echo  Starting AgriPredict AI FastAPI Backend...
echo ========================================================
set PYTHONPATH=%~dp0;%PYTHONPATH%
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause

