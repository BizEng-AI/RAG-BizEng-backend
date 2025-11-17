@echo off
cd /d C:\Users\sanja\rag-biz-english\server
python admin_fix_and_token.py yoo@gmail.com
if exist admin_fix_result.json (
    type admin_fix_result.json
) else (
    echo ERROR: admin_fix_result.json not created
)

