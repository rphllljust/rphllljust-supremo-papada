@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "FRONTEND_ROOT=%%~fI"

where npm.cmd >nul 2>nul
if errorlevel 1 (
    echo npm.cmd nao foi encontrado no PATH. Instale o Node.js/NPM antes de rodar o frontend.
    exit /b 1
)

pushd "%FRONTEND_ROOT%"

if not exist node_modules (
    echo node_modules nao encontrado. Instalando dependencias...
    call npm.cmd install
    if errorlevel 1 (
        popd
        exit /b 1
    )
)

call npm.cmd run dev -- --port 5173
set "EXIT_CODE=%ERRORLEVEL%"

popd
exit /b %EXIT_CODE%