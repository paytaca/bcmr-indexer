#!/bin/sh

wait-for-it.sh -t 60 $POSTGRES_HOST:$POSTGRES_PORT
python /app/manage.py migrate sessions
python /app/manage.py migrate
python /app/manage.py collectstatic --noinput

exec "$@"
