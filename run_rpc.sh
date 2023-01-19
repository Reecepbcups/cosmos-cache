#!/bin/sh
# chmod +x run_rpc.sh
# code /lib/systemd/system/juno_rpc.service
# [Unit]
# Description=My Shell Script
# [Service]
# ExecStart=/root/python-rpc-cache/run_rpc.sh
# [Install]
# WantedBy=multi-user.target
#
# sudo systemctl daemon-reload 
# sudo systemctl restart juno_rpc.service
# sudo systemctl start juno_rpc.service
# sudo systemctl enable juno_rpc.service
# sudo systemctl status juno_rpc.service

WORKERS=${WORKERS:-12}

cd /root/python-rpc-cache
gunicorn --workers $WORKERS --bind 0.0.0.0:5001 rpc:rpc_app