@echo off
echo ========================================================
echo  Starting AgriPredict AI Streamlit Dashboard...
echo ========================================================
set PYTHONPATH=%~dp0;%PYTHONPATH%
streamlit run %~dp0frontend\app.py
pause

