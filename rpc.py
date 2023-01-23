# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests websockets
# pip install --upgrade urllib3
# ----------------------------------------------

import asyncio
import json
import os
from os import getenv

import redis
import requests
import websockets
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_caching import Cache
from flask_cors import CORS, cross_origin
from flask_sock import Sock
from flask_socketio import SocketIO, emit  # flask_socketio

current_dir = os.path.dirname(os.path.realpath(__file__))

load_dotenv(os.path.join(current_dir, ".env"))

port = int(getenv("RPC_PORT", 5001))

RPC_URL = getenv("RPC_URL", "https://juno-rpc.reece.sh:443")
BASE_RPC = RPC_URL.replace("https://", "").replace("http://", "").replace(":443", "")

CACHE_SECONDS = int(getenv("CACHE_SECONDS", 7))

data_websocket = f'ws://{getenv("WEBSOCKET_ADDR", "15.204.143.232:26657")}/websocket'

RPC_DOMAIN = getenv("RPC_DOMAIN", "localhost:5001")

# replace RPC text to the updated domain
RPC_ROOT_HTML = requests.get(f"{RPC_URL}/").text.replace(BASE_RPC, RPC_DOMAIN)

rpc_app = Flask(__name__)
sock = Sock(rpc_app)
socketio = SocketIO(rpc_app)
cors = CORS(rpc_app, resources={r"/*": {"origins": "*"}})

redis_url = getenv("CACHE_REDIS_URL", "redis://127.0.0.1:6379/0")
rDB = redis.Redis.from_url(redis_url)

@rpc_app.route("/", methods=["GET"])
@cross_origin()
def get_all_rpc():
    return RPC_ROOT_HTML


@rpc_app.route("/<path:path>", methods=["GET"])
@cross_origin()
def get_rpc_endpoint(path):
    url = f"{RPC_URL}/{path}"
    args = request.args    

    key = f"{url};{args}"

    v = rDB.get(key)    
    if v:        
        # return v.decode("utf-8")
        return jsonify(json.loads(v.decode("utf-8")))

    req = requests.get(url, params=args)

    rDB.setex(key, CACHE_SECONDS, json.dumps(req.json()))

    return req.json()

@rpc_app.route("/", methods=["POST"])
@cross_origin()
def post_endpoint():    
    REQ_DATA: dict = request.get_json()

    method, params = REQ_DATA.get("method", None), REQ_DATA.get("params", None)
    key = f"{method}{params}"    
    
    v = rDB.get(key)    
    if v:
        # print("cache hit")
        # return v.decode("utf-8")
        return jsonify(json.loads(v.decode("utf-8")))

    # make req
    req = requests.post(f"{RPC_URL}", data=json.dumps(REQ_DATA))    
  
    rDB.setex(key, CACHE_SECONDS, json.dumps(req.json()))

    return req.json()


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


if __name__ == "__main__":
    rpc_app.run(debug=True, host="0.0.0.0", port=port)
