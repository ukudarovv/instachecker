@echo off
REM Быстрая проверка Instagram аккаунта (Windows)
REM Использование: quick_check.bat username

python quick_check.py %*

if errorlevel 3 (
    echo.
    echo [ERROR] Произошла ошибка при проверке
    pause
    exit /b 3
)

if errorlevel 2 (
    echo.
    echo [UNKNOWN] Не удалось определить статус
    pause
    exit /b 2
)

if errorlevel 1 (
    echo.
    echo [NOT FOUND] Аккаунт не найден
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Проверка завершена
pause
exit /b 0

