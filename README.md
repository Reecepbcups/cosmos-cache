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

## Requirements

- A Cosmos RPC / REST server endpoint (state synced, full node, or archive).
- A Redis server (local, or remote).
- A reverse proxy (to forward subdomain -> the endpoint cache on a machine)

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
```

## Installation

open `run_rpc.sh` and `./run_rest.sh`
Create the Systemd service files, then start with the preferred variable settings.
...

---

## Nginx / Reverse Proxy

Your normal NGINX configs work here, so long as it points / round robins to the exposed application ports
(5000 and 5001 by default in the .env file)

---

## Documentation

### Variable Length Cache

In the `cache_times.json` file, you can specify specific endpoints and how long said queries should persist in the cache.
This is useful for large queries such as /validators which may return 100+ validators. This data does not change often, making it useful for caching for longer periods of time.

If you wish to disable the cache, you can set the value to 0 for the said endpoint. If you wish to disable the endpoint query entirely, set it to a value less than 0 (such as -1).
By default, the cosmos/auth/v1beta1/accounts endpoint is disabled, as it temporarily halts the node.

This file uses regex pattern matching as keys, with values as the number of seconds to cache once it has been called.
For python strings, you must prefix any `*` you find with a `.`. So to match "random" in "my 8 random11 string", you would do `.*random.*` to match all before and after.

This is ONLY the path, which means it does not start with a `/`.
