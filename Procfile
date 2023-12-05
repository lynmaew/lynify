release: python manage.py migrate
web: python lynify/apps/polling_standalone.py & gunicorn lynify.wsgi & wait -n
