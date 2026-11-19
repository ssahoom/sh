@echo off
chcp 65001 > nul
echo ========================================================
echo  Connect AI LAB - Antigravity IDE / VS Code 직접 설치기
echo ========================================================

set "SRC_DIR=%~dp0imported_source\connect-ai-1.0.10"
set "EXT_NAME=connect-ai-lab-1.0.10"

echo [1] 확장 프로그램 폴더로 직접 복사 설치를 시작합니다...

set INSTALLED=0

:: Antigravity IDE 확인 및 설치
if exist "%USERPROFILE%\.antigravity-ide" (
    if not exist "%USERPROFILE%\.antigravity-ide\extensions" mkdir "%USERPROFILE%\.antigravity-ide\extensions"
    echo   - Antigravity IDE 에 설치 중...
    xcopy "%SRC_DIR%" "%USERPROFILE%\.antigravity-ide\extensions\%EXT_NAME%\" /E /I /Y /Q > nul
    echo     ✅ Antigravity IDE 설치 완료!
    set INSTALLED=1
)

:: VS Code 확인 및 설치
if exist "%USERPROFILE%\.vscode" (
    if not exist "%USERPROFILE%\.vscode\extensions" mkdir "%USERPROFILE%\.vscode\extensions"
    echo   - VS Code 에 설치 중...
    xcopy "%SRC_DIR%" "%USERPROFILE%\.vscode\extensions\%EXT_NAME%\" /E /I /Y /Q > nul
    echo     ✅ VS Code 설치 완료!
    set INSTALLED=1
)

:: Cursor 확인 및 설치
if exist "%USERPROFILE%\.cursor" (
    if not exist "%USERPROFILE%\.cursor\extensions" mkdir "%USERPROFILE%\.cursor\extensions"
    echo   - Cursor 에 설치 중...
    xcopy "%SRC_DIR%" "%USERPROFILE%\.cursor\extensions\%EXT_NAME%\" /E /I /Y /Q > nul
    echo     ✅ Cursor 설치 완료!
    set INSTALLED=1
)

if %INSTALLED%==0 (
    echo   - 기본 .vscode 폴더를 생성하고 설치합니다...
    if not exist "%USERPROFILE%\.vscode\extensions" mkdir "%USERPROFILE%\.vscode\extensions"
    xcopy "%SRC_DIR%" "%USERPROFILE%\.vscode\extensions\%EXT_NAME%\" /E /I /Y /Q > nul
    echo     ✅ 기본 설치 완료!
)

echo.
echo ========================================================
echo 🎉 설치가 성공적으로 완료되었습니다!
echo.
echo [사용 방법]
echo 1. IDE 창으로 돌아가 Ctrl + R 을 누르거나 IDE를 재시작하세요.
echo 2. 왼쪽 사이드바에 [Connect AI LAB] 로봇 아이콘(🤖)이 나타납니다.
echo ========================================================
pause

