release: python manage.py migrate
web: python poll.py & gunicorn lynify.wsgi & wait -n
