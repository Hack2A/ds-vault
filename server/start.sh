
set -e

echo "=== Running Django migrations ==="
python manage.py migrate --noinput

echo "=== Starting Django dev server ==="
exec python manage.py runserver 0.0.0.0:8000
