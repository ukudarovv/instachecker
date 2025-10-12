#!/bin/bash
# Start Django Mini App server

cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations (not needed but just in case)
python manage.py migrate --run-syncdb 2>/dev/null || true

# Start server
echo "🚀 Starting Mini App server on port 8001..."
echo "📱 Access at: http://localhost:8001"
echo ""
echo "⚠️  For production use HTTPS with gunicorn:"
echo "   gunicorn miniapp.wsgi:application --bind 0.0.0.0:8001"
echo ""

python manage.py runserver 0.0.0.0:8001

