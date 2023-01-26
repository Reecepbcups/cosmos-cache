#!/bin/sh
# https://www.awright.io/posts/7/running-multiple-instances-of-gunicorn-with-systemd
# 
# chmod +x rest/run_rest.sh
#
# code /lib/systemd/system/juno_rest.service
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
# WorkingDirectory=/root/python-rpc-cache/rest/%i
# ExecStart=/root/python-rpc-cache/run_rest.sh
# [Install]
# WantedBy=gunicorn.target
#
# sudo systemctl daemon-reload 
# sudo systemctl restart juno_rest.service
# sudo systemctl start juno_rest.service
# sudo systemctl stop juno_rest.service
# sudo systemctl enable juno_rest.service
# sudo systemctl status juno_rest.service

WORKERS=${WORKERS:-8}
THREADS=${THREADS:-4}

cd /root/python-rpc-cache/rest
gunicorn --workers $WORKERS --threads $THREADS --preload --bind 0.0.0.0:5000 rest:app

# python3 rest.py