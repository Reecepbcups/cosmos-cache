# Reece Williams | https://reece.sh | Jan 2023

# import asyncio
import json
import re

# import websockets
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from flask_sock import Sock

import CONFIG as CONFIG
from CONFIG import REDIS_DB
from HELPERS import hide_data, increment_call_value, replace_rpc_text
from RequestsHandler import RPCHandler

# from flask_socketio import emit


# === FLASK ===
rpc_app = Flask(__name__)
sock = Sock(rpc_app)
cors = CORS(rpc_app, resources={r"/*": {"origins": "*"}})

RPC_ROOT_HTML: str
RPC_HANDLER: RPCHandler


@rpc_app.before_first_request
def before_first_request():
    global RPC_ROOT_HTML, RPC_HANDLER
    CONFIG.update_cache_times()
    RPC_ROOT_HTML = replace_rpc_text()
    RPC_HANDLER = RPCHandler()


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
    key = f"{CONFIG.RPC_PREFIX};cache_times"
    v = REDIS_DB.get(key)
    if v:
        return jsonify(json.loads(v))

    CONFIG.update_cache_times()

    REDIS_DB.setex(key, 15 * 60, json.dumps(CONFIG.cache_times))
    return jsonify(CONFIG.cache_times)


def hide_rpc_data(res: dict, endpoint_path: str):
    if endpoint_path.lower().startswith("status"):
        res = hide_data(res, "result.node_info.listen_addr", CONFIG.RPC_LISTEN_ADDRESS)
        res = hide_data(res, "result.node_info.moniker", CONFIG.NODE_MONIKER)
        res = hide_data(res, "result.node_info.version", CONFIG.NODE_TM_VERSION)

    return res


@rpc_app.route("/<path:path>", methods=["GET"])
@cross_origin()
def get_rpc_endpoint(path: str):
    global total_calls

    args = request.args

    key = f"{CONFIG.RPC_PREFIX};{path};{args}"

    cache_seconds = CONFIG.get_cache_time_seconds(path, is_rpc=True)
    if cache_seconds < 0:
        return jsonify(
            {
                "error": f"cosmos endpoint cache: The path '{path}' is disabled on this node..."
            }
        )

    v = REDIS_DB.get(key)
    if v:
        increment_call_value("total_cache;get_rpc_endpoint")
        return jsonify(json.loads(v))

    res = RPC_HANDLER.handle_single_rpc_get_requests(path, key, cache_seconds, args)
    res = hide_rpc_data(res, path)

    return jsonify(res)


@rpc_app.route("/", methods=["POST"])
@cross_origin()
def post_rpc_endpoint():
    REQ_DATA = request.get_json()

    # BatchHTTPClient's send in a list of JSONRPCRequests
    if isinstance(REQ_DATA, list):
        increment_call_value("total_outbound;post_endpoint", amount=len(REQ_DATA))
        return jsonify(RPC_HANDLER.handle_batch_http_request(REQ_DATA))

    # If its a single RPC request, the following is used.
    method = REQ_DATA.get("method", None)
    params = REQ_DATA.get("params", None)
    key = f"{CONFIG.RPC_PREFIX};{method};{params}"

    cache_seconds = CONFIG.get_cache_time_seconds(method, is_rpc=True)
    if cache_seconds < 0:
        return jsonify(
            {
                "error": f"cosmos endpoint cache: The RPC method '{method}' is disabled on this node..."
            }
        )

    v = REDIS_DB.get(key)
    if v:
        increment_call_value("total_cache;post_endpoint")
        return jsonify(json.loads(v))

    res = RPC_HANDLER.handle_single_rpc_post_request(
        json.dumps(REQ_DATA), key, cache_seconds
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
    rpc_app.run(debug=True, host="0.0.0.0", port=CONFIG.RPC_PORT)
