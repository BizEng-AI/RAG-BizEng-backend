@echo off
echo ========================================
echo Starting BizEng Server on Port 8020
echo ========================================
echo.
cd /d C:\Users\sanja\rag-biz-english\server
echo Current directory: %CD%
echo.
echo Starting uvicorn...
echo.
uvicorn app:app --host 0.0.0.0 --port 8020 --reload

