# python-rpc-cache

## request -> nginx -> RPC_CACHE -> Juno Node.

## websocket -> nginx -> RPC_CACHE -> Juno Node. as well via bridge passth

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
