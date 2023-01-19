#!/bin/sh
WORKERS=${WORKERS:-4}

gunicorn --workers $WORKERS --bind 0.0.0.0:5001 rpc:rpc_app