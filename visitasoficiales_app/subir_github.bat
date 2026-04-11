@echo off
chcp 65001 >nul
echo ============================================================
echo   VISITAS OFICIALES APP — Subir a GitHub
echo ============================================================
echo.

REM Verificar que git esta instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git no encontrado. Instala Git desde:
    echo         https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Git detectado:
git --version
echo.

REM Pedir datos al usuario
set /p REPO_URL="Pega la URL de tu repositorio GitHub (ej: https://github.com/tuusuario/visitasoficiales): "
set /p USUARIO="Tu nombre de usuario de GitHub: "
set /p EMAIL="Tu email de GitHub: "
echo.

REM Configurar identidad de git
git config user.name "%USUARIO%"
git config user.email "%EMAIL%"

REM Inicializar repositorio si no existe
if not exist ".git" (
    echo [1/5] Inicializando repositorio Git...
    git init
    git branch -M main
) else (
    echo [1/5] Repositorio Git ya inicializado.
)
echo.

REM Agregar remote si no existe
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo [2/5] Conectando con GitHub...
    git remote add origin %REPO_URL%
) else (
    echo [2/5] Remote origin ya configurado. Actualizando URL...
    git remote set-url origin %REPO_URL%
)
echo.

REM Crear .gitignore de venv si no existe en el .gitignore raiz
echo [3/5] Verificando .gitignore...
findstr /c:"venv/" .gitignore >nul 2>&1
if %errorlevel% neq 0 (
    echo venv/ >> .gitignore
    echo __pycache__/ >> .gitignore
    echo *.pyc >> .gitignore
)
echo        .gitignore OK
echo.

REM Agregar archivos (excluyendo venv y fotos grandes)
echo [4/5] Preparando archivos para commit...
git add app.py
git add requirements.txt
git add .gitignore
git add modules\
git add data\
REM Las fotos se suben solo si pesan menos de 100MB (limite de GitHub)
REM Si tienes fotos grandes, considera Git LFS
git add assets\fotos\*.jpg 2>nul
git add assets\fotos\*.png 2>nul
git add assets\fotos\.gitkeep 2>nul
git add setup_y_ejecutar.bat
echo.

REM Mostrar estado antes del commit
git status
echo.

REM Hacer commit
set FECHA=%date:~6,4%-%date:~3,2%-%date:~0,2%
git commit -m "feat: app visitas oficiales prueba funcional - %FECHA%"
echo.

REM Subir a GitHub
echo [5/5] Subiendo a GitHub...
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo [AVISO] Si fallo el push, puede ser por autenticacion.
    echo         GitHub ya no acepta contrasenas, usa un Personal Access Token:
    echo         1. Ve a GitHub > Settings > Developer settings > Personal access tokens
    echo         2. Genera un token con permiso "repo"
    echo         3. Usa el token como contrasena cuando Git lo pida
    echo.
    echo         O configura SSH: https://docs.github.com/es/authentication
)

echo.
echo ============================================================
echo   Listo. Revisa tu repositorio en:
echo   %REPO_URL%
echo ============================================================
echo.
pause
