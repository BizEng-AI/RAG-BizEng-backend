@echo off
echo ========================================
echo QDRANT CLOUD INGESTION
echo ========================================
echo.
echo This will ingest all 3 books to Qdrant Cloud
echo Estimated cost: ^<$0.02 USD
echo Estimated time: 10-15 minutes
echo.
echo Books to ingest:
echo   1. book_1_ocr.txt (~1,200 vectors)
echo   2. book_2_ocr.txt (~400 vectors)
echo   3. book_3_ocr.txt (~2,000 vectors)
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Setting CONFIRM_INGEST=yes...
set CONFIRM_INGEST=yes

echo.
echo Starting ingestion...
echo.

cd /d C:\Users\sanja\rag-biz-english\server
python ingest_all.py

echo.
echo ========================================
echo INGESTION COMPLETE!
echo ========================================
echo.
echo Verifying collection...
python setup_qdrant.py

echo.
pause

