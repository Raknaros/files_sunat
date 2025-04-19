@echo off
echo ======================================
echo    ORGANIZADOR DE ARCHIVOS SUNAT
echo ======================================

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH.
    echo Instale Python y vuelva a intentarlo.
    pause
    exit /b 1
)

REM Solicitar directorios de origen y destino
set /p ORIGEN=Ingrese la carpeta donde buscar documentos SUNAT: 
set /p DESTINO=Ingrese la carpeta donde organizar los documentos: 

REM Verificar que los directorios existen
if not exist "%ORIGEN%" (
    echo ERROR: La carpeta de origen no existe.
    pause
    exit /b 1
)

REM Solicitar la extensión de archivos a buscar
set /p EXTENSION=Ingrese la extensión de los archivos a buscar (por defecto .pdf): 

REM Si no se ingresó una extensión, usar .pdf
if "%EXTENSION%"=="" set EXTENSION=.pdf

REM Ejecutar el organizador
echo.
echo Iniciando la organización de archivos...
echo.

python sunat_organizer.py --origen "%ORIGEN%" --destino "%DESTINO%" --extension %EXTENSION%

echo.
echo ======================================
echo Presione cualquier tecla para salir...
pause > nul 