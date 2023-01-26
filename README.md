# cosmos-endpoint-cache

Optimize Cosmos query calls by caching responses with a local or remote database.

This program sits on top of another server and acts as a middleware proxy between the requesting client and the actual cosmos RPC/API server.

## Requirements

- A Cosmos RPC / REST server endpoint (state synced, full node, or archive).
- A Redis server (local, or remote).
- A reverse proxy (to forward subdomain -> the endpoint cache on a machine)

---

## Setup

```bash
python -m pip install -r requirements.txt --upgrade
```

### Redis

```sh
sudo apt install redis-server

sudo pacman -Sy redis-server

systemctl start redis
systemctl enable redis
```

### or docker

```sh
docker run -d --name redis -p 6379:6379 redis
```

### or Akash (docker)

[Cloudmos.io Deploy Tool](https://cloudmos.io/cloud-deploy)
[Akash Deploy File](https://github.com/akash-network/awesome-akash/blob/master/redis/deploy.yaml)

## Installation

open `run_rpc.sh` and `./rest/run_rest.sh`
Create the Systemd service files, then start with the preferred variable settings.
...

---

## Nginx / Reverse Proxy

docs here...

---

## Documentation

### Variable Length Cache

In the `cache_times.json` file, you can specify specific endpoints and how long said queries should persist in the cache.
This is useful for large queries such as /validators which may return 100+ validators. This data does not change often, making it useful for caching for longer periods of time.

If you wish to disable the cache, you can set the value to 0 for said endpoint. If you wish to disable the endpoint query entirely, set to a value less than 0 (such as -1).
By default the cosmos/auth/v1beta1/accounts endpoint is disabled, as it temporarily halts the node.

This file uses regex pattern matching as keys, with values as the number of seconds to cache once it has been called.
For python strings, you must prefix any `*` you find with a `.`. So to match "random" in "my 8 random11 string", you would do `.*random.*` to match all before and after.

This is ONLY the path, which means it does not start with a `/`.
