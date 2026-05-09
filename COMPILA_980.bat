@echo off
title COMPILATORE 980 INSTASCRAPE PRO
echo ===================================================
echo   980 INSTASCRAPE PRO - GENERATORE ESEGUIBILE
echo ===================================================
echo.

echo [0/4] Chiusura processi esistenti...
taskkill /F /IM 980_INSTASCRAPE_PRO.exe /T >nul 2>&1

echo [1/4] Controllo dipendenze compilatore...
pip install pyinstaller pillow selenium --quiet

echo [2/4] Avvio compilazione (One-File Mode + Selenium Fix)...
echo Attendi, l'operazione potrebbe richiedere un minuto...
echo.

pyinstaller --noconfirm --onefile --windowed ^
 --add-data "index.html;." ^
 --add-data "instaloader;instaloader" ^
 --add-data "logo.png;." ^
 --collect-all "selenium" ^
 --collect-submodules "tkinter" ^
 --collect-submodules "PIL" ^
 --icon="logo.png" ^
 --name "980_INSTASCRAPE_PRO" ^
 main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [3/4] Pulizia file temporanei...
    rd /s /q build
    del /q 980_INSTASCRAPE_PRO.spec
    echo.
    echo [4/4] COMPILAZIONE COMPLETATA CON SUCCESSO!
    echo.
    echo ===================================================
    echo  IL TUO EXE E' PRONTO NELLA CARTELLA: \dist
    echo ===================================================
) else (
    echo.
    echo ###################################################
    echo  ERRORE DURANTE LA COMPILAZIONE!
    echo  Il file potrebbe essere ancora in uso.
    echo  Assicurati di aver chiuso ogni finestra dell'app.
    echo ###################################################
)

pause
