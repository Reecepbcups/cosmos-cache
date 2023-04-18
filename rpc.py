# Reece Williams | https://reece.sh | Jan 2023

import json
import logging
import os
import re
import threading

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS, cross_origin
from flask_sock import Sock

import CONFIG as CONFIG
from COINGECKO import Coingecko
from CONFIG import KV_STORE
from CONNECT_WEBSOCKET import TendermintRPCWebSocket
from HELPERS import (
    Mode,
    hide_rpc_data,
    increment_call_value,
    replace_rpc_text,
    ttl_block_only,
)
from HELPERS_TYPES import CallType
from RequestsHandler import RPCHandler

# === FLASK ===
rpc_app = Flask(__name__)

sock = Sock(rpc_app)
cors = CORS(rpc_app, resources={r"/*": {"origins": "*"}})

RPC_ROOT_HTML: str
RPC_HANDLER: RPCHandler

GECKO: Coingecko


@rpc_app.before_first_request
def before_first_request():
    global RPC_ROOT_HTML, RPC_HANDLER, GECKO
    CONFIG.update_cache_times()
    RPC_ROOT_HTML = replace_rpc_text()
    RPC_HANDLER = RPCHandler()
    GECKO = Coingecko()

    # future: https://stackoverflow.com/questions/24101724/gunicorn-with-multiple-workers-is-there-an-easy-way-to-execute-certain-code-onl

    if len(CONFIG.RPC_WEBSOCKET) > 0:
        tmrpc = TendermintRPCWebSocket(enableSignal=False, logLevel=logging.DEBUG)
        t = threading.Thread(target=tmrpc.ws.run_forever, kwargs={"reconnect": 5})
        t.daemon = True
        t.start()


# === ROUTES ===
@rpc_app.route("/", methods=["GET"])
@cross_origin()
def root():
    # get the data between :// and the final /
    base = re.search(r"\/\/.*\/", request.base_url).group(0)
    # remove any /'s
    base = base.replace("/", "")

    # </a><br><br>Endpoints that require arguments:<br><a href="//rpc.juno.website.xyz = rpc.juno.website.xyz
    rpc_url = re.search(
        r'(?<=:<br><a href="//)(.*?)(?=/abci_info\?">)', RPC_ROOT_HTML
    ).group(0)

    return RPC_ROOT_HTML.replace(rpc_url, base).replace("{BASE_URL}", base)


@rpc_app.route("/cache_info", methods=["GET"])
@cross_origin()
def cache_info():
    """
    Updates viewable cache times (seconds) at DOMAIN/cache_info.
    Auto updates for this program on update/change automatically without restart.

    We only store the data so any time its requested every X minutes, we regenerate the data.
    """
    key = f"rpc;cache_times"

    # v = REDIS_DB.get(key)
    # if v:
    #     return jsonify(json.loads(v))
    v = KV_STORE.get(key)
    if v:
        # we can just return v right? (if we save it as json)
        return jsonify(v)

    CONFIG.update_cache_times()

    # REDIS_DB.setex(key, 15 * 60, json.dumps(CONFIG.cache_times))
    KV_STORE.set(key, CONFIG.cache_times, 15 * 60)
    return jsonify(CONFIG.cache_times)


@rpc_app.route("/prices", methods=["GET"])
@cross_origin()
def coingecko():
    """
    Gets the prices from coingecko as defined in the .env file.
    """
    if CONFIG.COINGECKO_ENABLED:
        # caching handled in the class
        return jsonify(GECKO.get_price())
    else:
        return jsonify({"error": "prices are not enabled on this node..."})


def use_redis_hashset(path):
    if any(
        path.startswith(x)
        for x in [
            "block?height=",
            "block_by_hash",
            "block_results",
            "block_search",
            "blockchain",
            "tx_search",
        ]
    ):
        return True
    return False


@rpc_app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(rpc_app.root_path, "static"),
        "favicon.png",
        mimetype="image/vnd.microsoft.icon",
    )


@rpc_app.route("/<path:path>", methods=["GET"])
@cross_origin()
def get_rpc_endpoint(path: str):
    global total_calls

    args = request.args

    cache_seconds = CONFIG.get_cache_time_seconds(path, is_rpc=True)
    if cache_seconds == Mode.DISABLED.value:
        return jsonify(
            {
                "error": f"cosmos endpoint cache: The path '{path}' is disabled on this node..."
            }
        )

    use_hset = use_redis_hashset(path)
    key = f"rpc;{ttl_block_only(cache_seconds)};{path}"
    if use_hset:
        # v = REDIS_DB.hget(key, str(args))
        v = KV_STORE.hget(key, str(args))
    else:
        key = f"{key};{args}"
        v = KV_STORE.get(key)

    if v:
        increment_call_value(CallType.RPC_GET_CACHE.value)
        return jsonify(json.loads(v))

    res = RPC_HANDLER.handle_single_rpc_get_requests(
        path, key, args, cache_seconds, use_hset
    )

    return jsonify(res)


@rpc_app.route("/", methods=["POST"])
@cross_origin()
def post_rpc_endpoint():
    REQ_DATA = request.get_json()

    # BatchHTTPClient's send in a list of JSONRPCRequests
    if isinstance(REQ_DATA, list):
        increment_call_value(CallType.RPC_POST_OUTBOUND.value, len(REQ_DATA))
        return jsonify(RPC_HANDLER.handle_batch_http_request(REQ_DATA))

    # If its a single RPC request, the following is used.
    method = REQ_DATA.get("method", None)

    cache_seconds = CONFIG.get_cache_time_seconds(method, is_rpc=True)
    if cache_seconds == Mode.DISABLED.value:
        return jsonify(
            {
                "error": f"cosmos endpoint cache: The RPC method '{method}' is disabled on this node..."
            }
        )

    use_hset = use_redis_hashset(method)
    key = f"rpc;{ttl_block_only(cache_seconds)};{method}"
    # We save/get requests data since it also has the id of said requests from json RPC.

    modified_data = dict(REQ_DATA)

    # This could also be a UUID
    original_req_id = dict(REQ_DATA).get("id", 0)

    # we set the save key as -1 id since that is not real. This way on requests we are forced to change it back to the original requests
    # this ensures we cache things such as status independent of the requested id.
    modified_data["id"] = -1

    if use_hset:
        v = KV_STORE.hget(key, str(modified_data))
    else:
        key = f"{key};{modified_data}"
        v = KV_STORE.get(key)

    if v:
        increment_call_value(CallType.RPC_POST_CACHE.value)
        # replace the id with the original id so the requests is valid and in the order requested.
        # else we get: Error: wrong ID: response ID (0) does not match request ID (1)
        v = json.loads(v)
        v["id"] = original_req_id
        return jsonify(v)

    res = RPC_HANDLER.handle_single_rpc_post_request(
        json.dumps(REQ_DATA), key, method, cache_seconds, use_hset
    )
    res = hide_rpc_data(res, method)

    return jsonify(res)


# === socket bridge ===

# return JSONRPC/websockets
# JSONRPC requests can be also made via websocket. The websocket endpoint is at /websocket, e.g. localhost:26657/websocket. Asynchronous RPC functions like event subscribe and unsubscribe are only available via websockets.
# https://github.com/hashrocket/ws
# grpcurl -plaintext -d "{\"address\":\"juno10r39fueph9fq7a6lgswu4zdsg8t3gxlq670lt0\"}" wss://juno-rpc.reece.sh/websocket cosmos.bank.v1beta1.Query/AllBalances
# grpcurl -plaintext -d "{\"address\":\"juno10r39fueph9fq7a6lgswu4zdsg8t3gxlq670lt0\"}" 15.204.143.232:9090 cosmos.bank.v1beta1.Query/AllBalances
# curl -X GET -H "Content-Type: application/json" -H "x-cosmos-block-height: 6619410" http://15.204.143.232:1317/cosmos/bank/v1beta1/balances/juno10r39fueph9fq7a6lgswu4zdsg8t3gxlq670lt0


# @sock.route("/websocket")
# def websocket(ws):
#     print("websocket connected")
#     async def handle_subscribe():
#         async with websockets.connect(CONFIG.RPC_WEBSOCKET) as websocket:
#             while True:
#                 # receive data from the websocket
#                 data = await websocket.recv()
#                 if data == "close" or data == None:
#                     emit("close", data)
#                     await websocket.close()
#                     break
#                 emit("message", data)
#     asyncio.run(handle_subscribe())


if __name__ == "__main__":
    before_first_request()

    # setting to True runs 2 processes
    rpc_app.run(debug=True, host="0.0.0.0", port=CONFIG.RPC_PORT)
