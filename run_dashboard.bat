@echo off
echo ========================================================
echo  Starting AgriPredict AI Streamlit Dashboard...
echo ========================================================
set PYTHONPATH=%~dp0AI_Agricultural_Market_Price_Prediction;%PYTHONPATH%
streamlit run %~dp0AI_Agricultural_Market_Price_Prediction\frontend\app.py
pause

