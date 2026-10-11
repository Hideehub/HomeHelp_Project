web: gunicorn wsgi:app --workers 3 --timeout 60 --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -
release: flask --app wsgi db upgrade
