@echo off
chcp 65001
echo 올리브영 리뷰 수집기 exe 빌드 시작...
echo.

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경을 활성화합니다...
    call venv\Scripts\activate.bat
)

REM Python 빌드 스크립트 실행
python build_exe.py

echo.
echo 빌드 완료! dist 폴더를 확인하세요.
pause 