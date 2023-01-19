# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests websockets
# pip install --upgrade urllib3
# ----------------------------------------------

import asyncio
import json
from os import getenv

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_caching import Cache
from flask_sock import Sock
from flask_socketio import SocketIO, disconnect, emit  # flask_socketio

# Multiple in the future to iterate over?
BASE = "juno-rpc.reece.sh"
RPC_URL = f"https://{BASE}:443"

WEBSOCKET_ADDR = "15.204.143.232:26657"  # ws://15.204.143.232:26657/websocket
data_websocket = f"ws://{WEBSOCKET_ADDR}/websocket"


RPC_ROOT = requests.get(f"{RPC_URL}/").text.replace(BASE, "localhost:5001")

# GENESIS = requests.get(f"{RPC_URL}/genesis?").json()

load_dotenv(".env")

app = Flask(__name__)
sock = Sock(app)
socketio = SocketIO(app)

cache = Cache(
    app,
    config={
        "CACHE_TYPE": getenv("CACHE_TYPE", "redis"),
        "CACHE_REDIS_HOST": getenv("CACHE_REDIS_HOST", "redis"),
        "CACHE_REDIS_PORT": int(getenv("CACHE_REDIS_PORT", "6379")),
        "CACHE_REDIS_DB": getenv("CACHE_REDIS_DB", ""),
        "CACHE_REDIS_URL": getenv("CACHE_REDIS_URL", "redis://redis:6379/0"),
        "CACHE_DEFAULT_TIMEOUT": int(getenv("CACHE_DEFAULT_TIMEOUT", "6")),
    },
)


@app.route("/", methods=["GET"])
@cache.cached(timeout=60 * 10, query_string=True, key_prefix="rpc_root")
def get_all_endpoints():
    return RPC_ROOT


@app.route("/<path:path>", methods=["GET"])
@cache.cached(timeout=7, query_string=True)
def get_endpoint(path):
    url = f"{RPC_URL}/{path}"
    print(url)

    try:
        r = requests.get(url)
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

import websockets


@sock.route("/websocket")
def websocket(ws):
    print("websocket connected")

    # connect to data_websocket in a new thread, but does not return when successful.
    async def connect():
        async with websockets.connect(data_websocket) as websocket:
            while True:
                # receive data from the websocket
                data = await websocket.recv()
                print(f"< {data}")

                if data == "close" or data == None:
                    await websocket.close()
                    break

                # return the data back from wss://juno-rpc.reece.sh/websocket, which is a `101 Switching Protocols` status code.
                # This is a JSONRPC subscribe request

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
    app.run(debug=True, host="0.0.0.0", port=5001)
