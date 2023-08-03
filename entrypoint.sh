#!/bin/sh

wait-for-it.sh -t 60 $POSTGRES_HOST:$POSTGRES_PORT
python /code/manage.py migrate sessions
python /code/manage.py makemigrations bcmr_main
python /code/manage.py migrate
python /code/manage.py collectstatic --noinput

exec "$@"
