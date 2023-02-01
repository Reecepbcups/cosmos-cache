#!/bin/sh
# 
# chmod +x run_rest.sh
#
# sudo nano /lib/systemd/system/juno_rest.service
#
# If you are running as root, `sudo python -m pip install -r requirements.txt`
#
# [Unit]
# Description=gunicorn rest
# After=network.target
# PartOf=gunicorn.target
# # Since systemd 235 reloading target can pass through
# ReloadPropagatedFrom=gunicorn.target
# [Service]
# User=root
# Group=root
# WorkingDirectory=/root/cosmos-endpoint-cache/%i
# ExecStart=/root/cosmos-endpoint-cache/run_rest.sh
# Environment=WORKERS=2
# Environment=WORKERS=4
# [Install]
# WantedBy=gunicorn.target
#
# sudo systemctl daemon-reload 
# sudo systemctl status juno_rest.service
# sudo systemctl start juno_rest.service
# sudo systemctl stop juno_rest.service
# sudo systemctl restart juno_rest.service
# sudo systemctl enable juno_rest.service

PORT=${PORT:-5000}

WORKERS=${WORKERS:-2}
THREADS=${THREADS:-4}
W_CONN=${W_CONN:-1000}
BACKLOG=${BACKLOG:-2048}

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $THIS_DIR

gunicorn --workers $WORKERS --threads $THREADS --worker-connections $W_CONN --backlog $BACKLOG --bind 0.0.0.0:$PORT --preload rest:app