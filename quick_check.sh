#!/bin/bash
# Быстрая проверка Instagram аккаунта (Linux/Mac)
# Использование: ./quick_check.sh username

python3 quick_check.py "$@"
exit_code=$?

case $exit_code in
    0)
        echo ""
        echo "[SUCCESS] Проверка завершена успешно"
        ;;
    1)
        echo ""
        echo "[NOT FOUND] Аккаунт не найден"
        ;;
    2)
        echo ""
        echo "[UNKNOWN] Не удалось определить статус"
        ;;
    3)
        echo ""
        echo "[ERROR] Произошла ошибка при проверке"
        ;;
    130)
        echo ""
        echo "[INTERRUPTED] Прервано пользователем"
        ;;
esac

exit $exit_code

