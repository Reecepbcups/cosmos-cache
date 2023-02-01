#!/bin/sh
#
# chmod +x run_rest.sh
#
# Directions ./docs/SYSTEMD_FILES.md 
#
# sudo systemctl daemon-reload 
# sudo systemctl start juno_rest.service

PORT=${PORT:-5000}

WORKERS=${WORKERS:-2}
THREADS=${THREADS:-4}
W_CONN=${W_CONN:-1000}
BACKLOG=${BACKLOG:-2048}

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $THIS_DIR

gunicorn --workers $WORKERS --threads $THREADS --worker-connections $W_CONN --backlog $BACKLOG --bind 0.0.0.0:$PORT --preload rest:app