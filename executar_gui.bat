@echo off
cd /d "%~dp0"

REM Tenta encontrar o Python
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        py --version >nul 2>&1
        if errorlevel 1 (
            echo Python nao encontrado!
            echo Por favor, instale o Python de https://www.python.org/
            pause
            exit /b 1
        ) else (
            set PYTHON_CMD=py
        )
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Executa o GUI
%PYTHON_CMD% gui_wrapper.py

if errorlevel 1 (
    echo.
    echo Erro ao executar o GUI!
    echo Certifique-se de que as dependencias estao instaladas: pip install -r requirements.txt
    echo.
    pause
)

