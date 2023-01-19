#!/bin/sh
WORKERS=${WORKERS:-4}

gunicorn --workers $WORKERS --bind 0.0.0.0:5000 rest:app