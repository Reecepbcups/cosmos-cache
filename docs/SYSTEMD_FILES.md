# System Files

Make sure you replace **NETWORK_RPC / NETWORK_REST** with your value. Ex: **juno_rpc**

## RPC

```bash
# allow the file to be executed
chmod +x run_rpc.sh

# If you are running as Group=root :
# `sudo python -m pip install -r requirements/requirements.txt --upgrade`
sudo nano /lib/systemd/system/NETWORK_RPC.service

# Ensure to change WorkingDirectory and ExecStart to your folder locations
# [ Threads are more important than Workers. Should be roughly <= (2xTHREADS)+1 ]

# ============
[Unit]
Description=gunicorn rpc
After=network.target
PartOf=gunicorn.target
ReloadPropagatedFrom=gunicorn.target
[Service]
User=root
Group=root
WorkingDirectory=/root/cosmos-endpoint-cache/%i
ExecStart=/root/cosmos-endpoint-cache/run_rpc.sh
Environment=WORKERS=4
Environment=THREADS=6
Environment=W_CONN=1000
Environment=BACKLOG=2048
[Install]
WantedBy=gunicorn.target
# ============

# Then you can start / stop / restart the service
sudo systemctl daemon-reload 

sudo systemctl start NETWORK_RPC.service
sudo systemctl enable NETWORK_RPC.service # start after reboot

# And restart it 1 time every night (~0s of downtime)
#
# crontab -e
# 0 8 * * * systemctl restart NETWORK_RPC
```

## REST

```bash
# allow the file to be executed
chmod +x run_rest.sh

# If you are running as Group=root :
# `sudo python -m pip install -r requirements/requirements.txt --upgrade`
sudo nano /lib/systemd/system/NETWORK_REST.service

# Ensure to change WorkingDirectory and ExecStart to your folder locations
# REST will get way less requests. So give as lot less resources

# ============
[Unit]
Description=gunicorn rpc
After=network.target
PartOf=gunicorn.target
ReloadPropagatedFrom=gunicorn.target
[Service]
User=root
Group=root
WorkingDirectory=/root/cosmos-endpoint-cache/%i
ExecStart=/root/cosmos-endpoint-cache/run_rest.sh
Environment=WORKERS=2
Environment=THREADS=2
Environment=W_CONN=1000
Environment=BACKLOG=2048
[Install]
WantedBy=gunicorn.target
# ============

# Then you can start / stop / restart the service
sudo systemctl daemon-reload 

sudo systemctl start NETWORK_REST.service
sudo systemctl enable NETWORK_REST.service
```
