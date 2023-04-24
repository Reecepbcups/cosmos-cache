<p align="center">
  <img src="https://user-images.githubusercontent.com/31943163/217985088-cfcf62b3-808f-4ae3-a7f3-8c8486d941c9.png" />
</p>

Optimize Cosmos query calls by caching responses with a local or remote database.

This program sits on top of another server and acts as a middleware between the requesting client and the actual cosmos RPC/API server.

It supports

- Variable length cache times (for both RPC methods & REST URL endpoints)
- Disable specific endpoints entirely from being queried (ex: REST API /accounts)
- Enable cache only until the next block (via Tendermint RPC event subscription)

- Cached RPC request
- Cached REST request

- Swagger + OpenAPI support (openapi.yml cached)
- HttpBatchClient (for RPC with Tendermint 0.34 client)
- Statistics (optional /stats endpoint with password)

- Websocket basic passthrough support for Keplr wallet (TODO)
- Index blocks (TODO)

## My Nodes running this
- <https://juno-rpc.reece.sh>
- <https://juno-api.reece.sh>

## Pre-Requirements

- A Cosmos RPC / REST server endpoint (state synced, full node, or archive).
- A reverse proxy (to forward subdomain -> the endpoint cache on a machine)

## Where to run

Ideally, you should run this on your RPC/REST Node for localhost queries. However, you can also run on other infra including on your reverse proxy itself, or another separate node.
This makes it possible to run on cloud providers like Akash, AWS, GCP, Azure, etc.

---

## Setup

```bash
python3 -m pip install -r requirements/requirements.txt --upgrade

# Edit the ENV file to your needs
cp configs/.env .env

# Update which endpoints you want to disable / allow (regex) & how long to cache each for.
cp configs/cache_times.json cache_times.json

# THen run to ensure it was setup correctly
python3 rest.py
# ctrl + c
python3 rpc.py
# ctrl + c

# If all is good, continue on.
# NOTE: You can only run 1 of each locally at a time because WSGI is a pain. Requires Systemd as a service to run both in parallel.

# Then point your NGINX / CADDY config to this port rather than the default 26657 / 1317 endpoints
```

## Running in Production

- [Systemd Files](./docs/SYSTEMD_FILES.md)
- [Akash](./docs/AKASH.md)

## Documentation

- [Configuration Values](./docs/CONFIG_VALUES.md)
