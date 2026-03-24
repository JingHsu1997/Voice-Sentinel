@echo off
REM Voice Sentinel - 完整啟動腳本
REM 此腳本自動啟動後端服務器和前端

echo.
echo ========================================================
echo   VOICE SENTINEL - Full Integration Startup
echo ========================================================
echo.

REM 檢查虛擬環境
if not exist ".venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .\.venv\Scripts\Activate.ps1
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM 啟動虛擬環境
call .\.venv\Scripts\activate.bat

REM 檢查依賴
echo [INFO] Checking dependencies...
python -c "import flask, flask_cors" 2>nul
if errorlevel 1 (
    echo [WARNING] Flask dependencies not found. Installing...
    pip install flask flask-cors
)

REM 啟動後端服務器
echo.
echo [INFO] Starting Flask API Server on http://localhost:5000
echo        Press Ctrl+C to stop the server
echo.
start cmd /k "python app.py"

REM 等待服務器啟動
timeout /t 2 /nobreak

REM 打開前端
echo.
echo [INFO] Opening frontend interface...
timeout /t 1 /nobreak
start ..\index.html

echo.
echo ========================================================
echo   Frontend opened in default browser
echo   Backend running at http://localhost:5000
echo   
echo   Ready to use! Click [REC] to start recording.
echo ========================================================
echo.
pause
