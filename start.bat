@echo off
echo ========================================
echo   CHATBOT BAERA - UMSA
echo   Powered by Google Gemini
echo ========================================
echo.

cd backend

REM Verificar archivo .env
if not exist "../config/.env" (
    echo [ERROR] No se encontro el archivo .env
    echo.
    echo Por favor:
    echo 1. Ve a la carpeta 'config'
    echo 2. Copia .env.example a .env
    echo 3. Agrega tu GOOGLE_API_KEY
    echo.
    echo Obten tu API key en: https://makersuite.google.com/app/apikey
    echo.
    pause
    exit /b 1
)

REM Copiar .env a backend
copy "..\config\.env" ".env" >nul

echo [1/2] Iniciando servidor Flask con Gemini...
echo.
echo Servidor corriendo en: http://localhost:5000
echo Presiona Ctrl+C para detener
echo.
echo [2/2] Logs del servidor:
echo ========================================
python app.py

pause
