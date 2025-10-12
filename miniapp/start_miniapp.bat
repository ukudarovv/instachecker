@echo off
REM Start Django Mini App server for Windows

cd /d "%~dp0"

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🚀 Starting Mini App server on port 8001...
echo 📱 Access at: http://localhost:8001
echo.
echo ⚠️  For production use HTTPS with gunicorn:
echo    gunicorn miniapp.wsgi:application --bind 0.0.0.0:8001
echo.

python manage.py runserver 0.0.0.0:8001

