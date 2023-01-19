# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests websockets
# pip install --upgrade urllib3
# ----------------------------------------------

import asyncio
import json
from os import getenv

import requests
import websockets
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_sock import Sock
from flask_socketio import SocketIO, disconnect, emit  # flask_socketio

port = int(getenv("RPC_PORT", 5001))

# Multiple in the future to iterate over?
BASE_RPC = getenv("BASE_RPC", "juno-rpc.reece.sh")

# BASE_RPC = "rpc.juno.strange.love"

# RPC_URL = f"https://{BASE_RPC}:443"
RPC_URL = getenv("RPC_URL", "https://{BASE}:443").replace("{BASE}", BASE_RPC)

WEBSOCKET_ADDR = getenv("WEBSOCKET_ADDR", "15.204.143.232:26657")
data_websocket = f"ws://{WEBSOCKET_ADDR}/websocket"

RPC_DOMAIN = getenv("RPC_DOMAIN", "localhost:5001")

RPC_ROOT = requests.get(f"{RPC_URL}/").text.replace(BASE_RPC, RPC_DOMAIN)

load_dotenv("../.env")

rpc_app = Flask(__name__)
sock = Sock(rpc_app)
socketio = SocketIO(rpc_app)

redis_host = getenv("CACHE_REDIS_HOST", "127.0.0.1")
redis_port = int(getenv("CACHE_REDIS_PORT", "6379"))
cache = Cache(
    rpc_app,
    config={
        "CACHE_TYPE": getenv("CACHE_TYPE", "redis"),
        "CACHE_REDIS_HOST": redis_host,
        "CACHE_REDIS_PORT": redis_port,
        "CACHE_REDIS_DB": getenv("CACHE_REDIS_DB", ""),
        "CACHE_REDIS_URL": getenv(
            "CACHE_REDIS_URL", f"redis://{redis_host}:{redis_port}/0"
        ),
        "CACHE_DEFAULT_TIMEOUT": int(getenv("CACHE_DEFAULT_TIMEOUT", "6")),
    },
)


@rpc_app.route("/", methods=["GET"])
@cache.cached(timeout=60 * 10, query_string=True, key_prefix="rpc_root")
def get_all_rpc():
    return RPC_ROOT


@rpc_app.route("/<path:path>", methods=["GET"])
@cache.cached(timeout=7, query_string=True)
def get_rpc_endpoint(path):
    url = f"{RPC_URL}/{path}"
    # print(url)
    try:
        r = requests.get(url)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)})


@rpc_app.route("/", methods=["POST"])
@cache.cached(timeout=7, query_string=True)
def post_endpoint():
    try:
        d = json.dumps(request.get_json())
        print(d)
        r = requests.post(f"{RPC_URL}", data=d)
        print(r.text)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)})


# === socket bridge ===

# return JSONRPC/websockets
# JSONRPC requests can be also made via websocket. The websocket endpoint is at /websocket, e.g. localhost:26657/websocket. Asynchronous RPC functions like event subscribe and unsubscribe are only available via websockets.
# https://github.com/hashrocket/ws
# grpcurl -plaintext -d "{\"address\":\"juno10r39fueph9fq7a6lgswu4zdsg8t3gxlq670lt0\"}" wss://juno-rpc.reece.sh/websocket cosmos.bank.v1beta1.Query/AllBalances
# flask jsonrpc_websocket /websocket endpoint, connect to data_websocket
# grpcurl -plaintext -d "{\"address\":\"juno10r39fueph9fq7a6lgswu4zdsg8t3gxlq670lt0\"}" 15.204.143.232:9090 cosmos.bank.v1beta1.Query/AllBalances
# curl -X GET -H "Content-Type: application/json" -H "x-cosmos-block-height: 6619410" http://15.204.143.232:1317/cosmos/bank/v1beta1/balances/juno10r39fueph9fq7a6lgswu4zdsg8t3gxlq670lt0


@sock.route("/websocket")
def websocket(ws):
    print("websocket connected")

    # connect to data_websocket in a new thread, but does not return when successful.
    # async def connect():
    #     async with websockets.connect(data_websocket) as websocket:
    #         while True:
    #             # receive data from the websocket
    #             data = await websocket.recv()
    #             print(f"< {data}")

    #             if data == "close" or data == None:
    #                 await websocket.close()
    #                 break

    #             # return the data back from wss://juno-rpc.reece.sh/websocket, which is a `101 Switching Protocols` status code.
    #             # This is a JSONRPC subscribe request

    async def handle_subscribe():
        async with websockets.connect(data_websocket) as websocket:
            while True:
                # receive data from the websocket
                data = await websocket.recv()
                if data == "close" or data == None:
                    emit("close", data)
                    await websocket.close()
                    break
                emit("message", data)

    asyncio.run(handle_subscribe())


# run
if __name__ == "__main__":
    rpc_app.run(debug=True, host="0.0.0.0", port=port)
