@echo off
cls
echo ========================================
echo   CHATBOT BAERA - UMSA
echo   Powered by Google Gemini
echo ========================================
echo.

REM Ir a la carpeta backend
cd /d "%~dp0backend"

REM Verificar que existe app.py
if not exist "app.py" (
    echo [ERROR] No se encontro app.py
    echo Asegurate de estar en la carpeta correcta
    pause
    exit /b 1
)

echo [INFO] Iniciando servidor...
echo.
echo Servidor: http://localhost:5000
echo Presiona Ctrl+C para detener
echo.
echo ========================================
echo.

REM Ejecutar el servidor
python app.py

REM Si hay error, pausar para ver el mensaje
if errorlevel 1 (
    echo.
    echo [ERROR] Hubo un problema al iniciar el servidor
    echo.
    pause
)
