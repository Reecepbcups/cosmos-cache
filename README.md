# cosmos-rpc-cache

Optimize Cosmos RPC calls by caching responses with Redis.
Both GET and POST

RPC only currently, REST in the future (Can't currently run both on the same machine. But will drastically speed up Swagger)

---

Install:

```sh
sudo apt install redis-server

sudo pacman -Sy redis-server

systemctl start redis
systemctl enable redis
```

or docker

```sh
# start redis server
docker run -d --name redis -p 6379:6379 redis
```

Run:

```
sh run.sh
```
