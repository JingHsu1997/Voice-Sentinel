#!/usr/bin/env powershell
# Voice Sentinel - Full Integration Startup Script (PowerShell)
# Usage: .\start.ps1

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "   VOICE SENTINEL - Full Integration Startup" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

# Check virtual environment
if (-not (Test-Path ".\.venv")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Check Flask dependencies
Write-Host "[INFO] Checking dependencies..." -ForegroundColor Cyan
try {
    python -c "import flask, flask_cors" 2>&1 | Out-Null
} catch {
    Write-Host "[WARNING] Flask dependencies not found. Installing..." -ForegroundColor Yellow
    pip install flask flask-cors
}

# Start backend server
Write-Host ""
Write-Host "[INFO] Starting Flask API Server on http://localhost:5000" -ForegroundColor Cyan
Write-Host "       Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start Flask in background
$flaskProcess = Start-Process python -ArgumentList "app.py" -PassThru -NoNewWindow

# Wait for server to start
Start-Sleep -Seconds 2

# Open frontend
Write-Host "[INFO] Opening frontend interface..." -ForegroundColor Cyan
Start-Sleep -Seconds 1
Start-Process "..\index.html"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "   ✅ Frontend opened in default browser" -ForegroundColor Green
Write-Host "   ✅ Backend running at http://localhost:5000" -ForegroundColor Green
Write-Host "   " -ForegroundColor Green
Write-Host "   Ready to use! Click [REC] to start recording." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

# Keep terminal open
Write-Host "Server is running. Press Ctrl+C in the Flask window to stop." -ForegroundColor Gray
Read-Host "Press Enter to exit this window"

# Kill backend if still running
Stop-Process -Id $flaskProcess.Id -ErrorAction SilentlyContinue
