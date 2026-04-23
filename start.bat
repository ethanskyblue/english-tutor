@echo off
chcp 65001 > nul
echo.
echo  ========================================
echo   🎓 English Tutor 웹앱 시작 중...
echo  ========================================
echo.

REM Flask 설치 확인
pip show flask >nul 2>&1
if errorlevel 1 (
    echo  Flask 설치 중...
    pip install flask
    echo.
)

REM 앱 실행
python app.py
pause
