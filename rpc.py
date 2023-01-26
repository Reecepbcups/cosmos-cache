# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests websockets
# pip install --upgrade urllib3
# ----------------------------------------------

import asyncio
import json
import os
import re
from os import getenv

import redis
import requests
import websockets
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from flask_sock import Sock
from flask_socketio import emit

FAVICON = """<link href="data:image/x-icon;base64,AAABAAEAEBAAAAAAAABoBQAAFgAAACgAAAAQAAAAIAAAAAEACAAAAAAAAAEAAAAAAAAAAAAAAAEAAAAAAAD///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" rel="icon" type="image/x-icon" />"""

current_dir = os.path.dirname(os.path.realpath(__file__))

load_dotenv(os.path.join(current_dir, ".env"))

port = int(getenv("RPC_PORT", 5001))

PREFIX = getenv("REDIS_RPC_PREFIX", "junorpc")

RPC_URL = getenv("RPC_URL", "https://juno-rpc.reece.sh:443")
BASE_RPC = getenv("BASE_RPC", "15.204.143.232:26657")

BACKUP_RPC_URL = getenv("BACKUP_RPC_URL", "https://rpc.juno.strange.love:443")
BACKUP_BASE_RPC = getenv("BACKUP_BASE_RPC", "rpc.juno.strange.love")

ENABLE_COUNTER = getenv("ENABLE_COUNTER", "true").lower().startswith("t")

data_websocket = f'ws://{getenv("WEBSOCKET_ADDR", "15.204.143.232:26657")}/websocket'

RPC_DOMAIN = getenv("RPC_DOMAIN", "localhost:5001")

# Load specific cache times (regex supported)
# with open(f"{current_dir}/cache_times.json", "r") as f:
#     cache_times: dict = json.loads(f.read())
# DEFAULT_CACHE_SECONDS = cache_times.get("DEFAULT", 6)
# ENDPOINTS = cache_times.get("rpc", {})

cache_times: dict = {}


def update_cache_times():
    """
    Updates any config variables which can be changed without restarting the server.
    Useful for the /cache_info endpoint & actually applying said cache changes at any time
    """
    global cache_times, DEFAULT_CACHE_SECONDS, ENDPOINTS
    with open(f"{current_dir}/cache_times.json", "r") as f:
        cache_times = json.loads(f.read())

    DEFAULT_CACHE_SECONDS = cache_times.get("DEFAULT", 6)
    ENDPOINTS = cache_times.get("rpc", {})


def replace_rpc_text() -> str:
    # Get RPC format, and replace with our domain values.
    try:
        RPC_ROOT_HTML = requests.get(f"{RPC_URL}/").text.replace(BASE_RPC, RPC_DOMAIN)
    except:
        RPC_ROOT_HTML = requests.get(f"{BACKUP_RPC_URL}/").text.replace(
            BACKUP_BASE_RPC, RPC_DOMAIN
        )

    RPC_TITLE = getenv("RPC_TITLE", "")
    if len(RPC_TITLE) > 0:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "<html><body>",
            f"<html><head><title>{RPC_TITLE}</title></head><body>",
        )

    # Puts text at the bottom, maybe put at the top in the future?
    RPC_CUSTOM_TEXT = getenv("RPC_CUSTOM_TEXT", "").replace(
        "{RPC_DOMAIN}", f"{RPC_DOMAIN}"
    )
    if len(RPC_CUSTOM_TEXT) > 0:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "Available endpoints:<br><br>",
            f"{RPC_CUSTOM_TEXT}<br>Available endpoints:<br><br>",
        )

    # add cache_info endpoint. THIS REMOVES BLANK Available endpoints:<br><br>
    RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
        "Available endpoints:<br><br>",
        f'<a href="//{RPC_DOMAIN}/cache_info">Cache Information</a><br><br>',
    )

    # add blank favicon
    if "<head>" in RPC_ROOT_HTML:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace("<head>", f"<head>{FAVICON}", 1)
    else:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "<html>", f"<html><head>{FAVICON}</head>", 1
        )

    return RPC_ROOT_HTML


# === APP ===
update_cache_times()
RPC_ROOT_HTML = replace_rpc_text()

# === FLASK ===
rpc_app = Flask(__name__)
sock = Sock(rpc_app)
cors = CORS(rpc_app, resources={r"/*": {"origins": "*"}})

# === REDIS ===
REDIS_URL = getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
rDB = redis.Redis.from_url(REDIS_URL)


@rpc_app.route("/", methods=["GET"])
@cross_origin()
def get_all_rpc():
    return RPC_ROOT_HTML


total_calls = {
    "total_cache;get_rpc_endpoint": 0,
    "total_outbound;get_rpc_endpoint": 0,
    #
    "total_cache;post_endpoint": 0,
    "total_outbound;post_endpoint": 0,
}

INC_EVERY = int(getenv("INCREASE_COUNTER_EVERY", 10))


def inc_value(key):
    global total_calls

    if ENABLE_COUNTER == False:
        return

    if key not in total_calls:
        total_calls[key] = 0

    if total_calls[key] >= INC_EVERY:
        rDB.incr(f"{PREFIX};{key}", amount=total_calls[key])
        total_calls[key] = 0
    else:
        total_calls[key] += 1


def get_cache_time_seconds(path: str) -> int:
    cache_seconds = DEFAULT_CACHE_SECONDS
    for k, v in ENDPOINTS.items():
        if re.match(k, path):
            cache_seconds = v
            break

    return cache_seconds


@rpc_app.route("/cache_info", methods=["GET"])
@cross_origin()
def get_cache_setings():
    """
    Updates viewable cache times (seconds) at DOMAIN/cache_info.
    Auto updates every 15 minutes for this program on update/change automatically without restart.
    """
    key = f"{PREFIX};cache_times"
    v = rDB.get(key)
    if v:
        return jsonify(json.loads(v.decode("utf-8")))

    update_cache_times()

    rDB.setex(key, 15 * 30, json.dumps(cache_times))
    return jsonify(cache_times)


@rpc_app.route("/<path:path>", methods=["GET"])
@cross_origin()
def get_rpc_endpoint(path):
    global total_calls

    url = f"{RPC_URL}/{path}"
    args = request.args

    key = f"{PREFIX};{url};{args}"

    v = rDB.get(key)
    if v:
        inc_value("total_cache;get_rpc_endpoint")
        return jsonify(json.loads(v.decode("utf-8")))

    try:
        req = requests.get(url, params=args)
    except Exception as e:
        print(e)
        req = requests.get(f"{BACKUP_RPC_URL}/{path}", params=args)

    cache_seconds = get_cache_time_seconds(path)

    rDB.setex(key, cache_seconds, json.dumps(req.json()))
    inc_value("total_outbound;get_rpc_endpoint")

    return req.json()


@rpc_app.route("/", methods=["POST"])
@cross_origin()
def post_endpoint():
    REQ_DATA: dict = request.get_json()

    method, params = REQ_DATA.get("method", None), REQ_DATA.get("params", None)
    key = f"{PREFIX};{method};{params}"

    v = rDB.get(key)
    if v:
        inc_value("total_cache;post_endpoint")
        return jsonify(json.loads(v.decode("utf-8")))

    # make req
    try:
        req = requests.post(f"{RPC_URL}", data=json.dumps(REQ_DATA))
    except:
        req = requests.post(f"{BACKUP_RPC_URL}", data=json.dumps(REQ_DATA))

    cache_seconds = get_cache_time_seconds(method)

    rDB.setex(key, cache_seconds, json.dumps(req.json()))
    inc_value("total_outbound;post_endpoint")

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
