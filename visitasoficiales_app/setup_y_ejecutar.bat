@echo off
chcp 65001 >nul
echo ============================================================
echo   VISITAS OFICIALES APP — Setup y Ejecucion
echo ============================================================
echo.

REM Verificar que Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ desde:
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Python detectado:
python --version
echo.

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo [2/4] Creando entorno virtual...
    python -m venv venv
    echo        Entorno virtual creado en: venv\
) else (
    echo [2/4] Entorno virtual ya existe. Reutilizando...
)
echo.

REM Activar entorno virtual
echo [3/4] Activando entorno virtual e instalando dependencias...
call venv\Scripts\activate.bat

REM Actualizar pip silenciosamente
python -m pip install --upgrade pip --quiet

REM Instalar dependencias
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo la instalacion de dependencias.
    echo         Revisa requirements.txt y tu conexion a internet.
    pause
    exit /b 1
)
echo.
echo [4/4] Lanzando la app en el navegador...
echo       Presiona Ctrl+C en esta ventana para detener el servidor.
echo.
echo ============================================================
echo   URL local: http://localhost:8501
echo ============================================================
echo.

streamlit run app.py

pause
