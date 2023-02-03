#!/bin/sh
#
# Directions ./docs/SYSTEMD_FILES.md 
#
# sudo systemctl daemon-reload 
# sudo systemctl start juno_rpc.service
#
# Restart nightly:
# crontab -e
# 0 8 * * * systemctl restart juno_rpc

PORT=${PORT:-5001}

WORKERS=${WORKERS:-4}
THREADS=${THREADS:-6}
W_CONN=${W_CONN:-1000}
BACKLOG=${BACKLOG:-2048}

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $THIS_DIR
# python3 -m pip install -r requirements/requirements.txt

gunicorn --workers $WORKERS --threads $THREADS --worker-connections $W_CONN --backlog $BACKLOG --bind 0.0.0.0:$PORT --preload rpc:rpc_app