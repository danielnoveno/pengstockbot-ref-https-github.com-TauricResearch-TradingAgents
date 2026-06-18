@echo off
echo ══════════════════════════════════════════════
echo   AI Trading Assistant
echo ══════════════════════════════════════════════

:: Check if .env exists
if not exist .env (
    echo.
    echo [!] File .env belum ada!
    echo     Copy .env.example ke .env dan isi API keys kamu.
    echo.
    copy .env.example .env
    echo     File .env sudah dibuat. Silakan edit dan isi API keys.
    pause
    exit /b 1
)

:: Install dependencies
echo.
echo [*] Install dependencies...
pip install -r requirements_assistant.txt -q

:: Run
echo.
echo [*] Menjalankan AI Trading Assistant...
echo     Dashboard: http://localhost:8080
echo     Tekan Ctrl+C untuk berhenti.
echo.
python -m trading_assistant.main
