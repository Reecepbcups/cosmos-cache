#!/bin/sh
# 
# chmod +x run_rpc.sh
#
# sudo nano /lib/systemd/system/juno_rpc.service
#
# If you are running as root, `sudo python -m pip install -r requirements.txt`
#
# [Unit]
# Description=gunicorn rpc
# After=network.target
# PartOf=gunicorn.target
# # Since systemd 235 reloading target can pass through
# ReloadPropagatedFrom=gunicorn.target
# [Service]
# User=root
# Group=root
# WorkingDirectory=/root/cosmos-endpoint-cache/%i
# ExecStart=/root/cosmos-endpoint-cache/run_rpc.sh
# [Install]
# WantedBy=gunicorn.target
#
# sudo systemctl daemon-reload 
# sudo systemctl status juno_rpc.service
# sudo systemctl start juno_rpc.service
# sudo systemctl stop juno_rpc.service
# sudo systemctl restart juno_rpc.service
# sudo systemctl enable juno_rpc.service

PORT=${PORT:-5001}

WORKERS=${WORKERS:-20}
THREADS=${THREADS:-2}
W_CONN=${W_CONN:-2}
BACKLOG=${BACKLOG:-2048}

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $THIS_DIR

gunicorn --workers $WORKERS --threads $THREADS --worker-connections $W_CONN --backlog $BACKLOG --bind 0.0.0.0:$PORT --preload rpc:rpc_app