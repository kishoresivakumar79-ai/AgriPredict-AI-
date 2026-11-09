@echo off
echo ========================================================
echo  Starting AgriPredict AI FastAPI Backend...
echo ========================================================
set PYTHONPATH=%~dp0AI_Agricultural_Market_Price_Prediction;%PYTHONPATH%
cd %~dp0AI_Agricultural_Market_Price_Prediction
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause

