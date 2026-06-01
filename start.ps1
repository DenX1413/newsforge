# Запуск бэкенда, фронтенда и Telegram-бота одновременно
Write-Host "Starting Spotika..." -ForegroundColor Cyan

# Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$PSScriptRoot\backend'
python -m uvicorn api:app --reload --port 8000
"@ -WindowStyle Normal

Start-Sleep -Seconds 2

# Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$PSScriptRoot\frontend'
npm run dev
"@ -WindowStyle Normal

# Telegram Bot
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$PSScriptRoot'
python telegram_bot.py
"@ -WindowStyle Normal

Write-Host ""
Write-Host "Backend:      http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend:     http://localhost:5173" -ForegroundColor Green
Write-Host "Telegram-бот: запущен (polling)" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to close..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
