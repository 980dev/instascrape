@echo off
title 980 INSTASCRAPE PRO
echo ========================================
echo       980 INSTASCRAPE - PRO ENGINE
echo ========================================
echo.
echo Avvio in corso...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Errore durante l'avvio. Controlla di aver installato i requisiti.
    pause
)
