#!/usr/bin/env bash
set -e

# wait for Postgres (external) if you like
if [ -n "$OEL_HOSTNAME" ] && [ -n "$OEL_PORT" ]; then
  echo "Waiting for Postgres at ${OEL_HOSTNAME}:${OEL_PORT}..."
  until nc -z $OEL_HOSTNAME $OEL_PORT; do
    sleep 0.1
  done
fi

# wait for Redis
if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
  echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
  until nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 0.1
  done
fi

# migrations + static
echo "Apply migrations and collect static files"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# dispatch to the right command
case "$1" in
  web)
    exec gunicorn oel.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 3 \
      --log-level info
    ;;
  celery)
    exec celery -A oel worker --loglevel=info
    ;;
  beat)
    exec celery -A oel beat --loglevel=info --scheduler=django_celery_beat.schedulers:DatabaseScheduler
    ;;
  *)
    # pass through any other command, e.g. "bash"
    exec "$@"
    ;;
esac
