# Cosmos Endpoint Cache

Optimize Cosmos query calls by caching responses with a local or remote database.

This program sits on top of another server and acts as a middleware proxy between the requesting client and the actual cosmos RPC/API server.

This program supports

- Variable length cache times (for both RPC methods & REST URL endpoints)
- Disable specific endpoints entirely from being queried (ex: REST API /accounts)

- Cached RPC request
- Cached REST request

- Swagger + OpenAPI support (openapi.yml cached)
- HttpBatchClient (for RPC with Tendermint 0.34 client)
- Statistics (optional /stats endpoint with password)

~~- Websocket basic passthrough support for Keplr wallet (TODO)~~
~~-Index blocks (TODO)~~

## Pre-Requirements

- A Cosmos RPC / REST server endpoint (state synced, full node, or archive).
- A Redis server (local, or remote).
- A reverse proxy (to forward subdomain -> the endpoint cache on a machine)

## Where to run

Ideally, you should run this on your RPC/REST Node for localhost queries. However, you can also run on other infra including on your reverse proxy itself, or another separate node.
This makes it possible to run on cloud providers like Akash, AWS, GCP, Azure, etc.

---

### Redis Install

```sh
# System
sudo apt install redis-server

sudo pacman -Sy redis-server

systemctl start redis
systemctl enable redis

# or Docker
docker run -d --name redis -p 6379:6379 redis
```

## Setup

```bash
python -m pip install -r requirements/requirements.txt --upgrade

# Edit the ENV file to your needs
cp configs/.env .env

# Update which endpoints you want to disable / allow (regex) & how long to cache each for.
cp configs/cache_times.json cache_times.json

# Optional: custom redis client configuration
cp configs/redis_config.json redis_config.json

# THen run to ensure it was setup correctly
python3 rest.py
# ctrl + c
python3 rpc.py
# ctrl + c

# If all is good, continue on.
# NOTE: You can only run 1 of each locally at a time because WSGI is a pain. Requires Systemd as a service to run both in parrallel.
```

## Running in Production

open `run_rpc.sh` and `./run_rest.sh`
Create the systemd service files, then start with the preferred variable settings.
---

## Nginx / Reverse Proxy

Your normal NGINX configs work here, so long as it points / round robins to the exposed application ports
(5000 and 5001 by default in the .env file)

---

## Documentation

- [Configuration Values](./docs/CONFIG_VALUES.md)
