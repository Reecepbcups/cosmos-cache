# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests
# pip install --upgrade urllib3
# ----------------------------------------------

import json
import re

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

import CONFIG
from CONFIG import REDIS_DB
from HELPERS import (
    download_openapi_locally,
    get_swagger_code_from_source,
    increment_call_value,
)

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


REST_SWAGGER_HTML = ""


@app.before_first_request
def before_first_request():
    CONFIG.update_cache_times()
    download_openapi_locally()


# if route is just /, return the openapi swagger ui
@app.route("/", methods=["GET"])
@cross_origin()
def root():
    global REST_SWAGGER_HTML

    if len(REST_SWAGGER_HTML) > 0:
        return REST_SWAGGER_HTML

    REST_SWAGGER_HTML = get_swagger_code_from_source()
    return REST_SWAGGER_HTML


@app.route("/stats", methods=["GET"])
@cross_origin()
def stats():
    # https://url/stats?password=123
    if (
        len(CONFIG.STATS_PASSWORD) > 0
        and request.args.get("password") != CONFIG.STATS_PASSWORD
    ):
        return "Invalid password"

    # gets information about the redis
    rest_cache = REDIS_DB.get(f"{CONFIG.REST_PREFIX};total_cache;get_all_rest")
    rest_outbound = REDIS_DB.get(f"{CONFIG.REST_PREFIX};total_outbound;get_all_rest")
    rpc_cache = REDIS_DB.get(f"{CONFIG.RPC_PREFIX};total_cache;get_rpc_endpoint")
    rpc_outbound = REDIS_DB.get(f"{CONFIG.RPC_PREFIX};total_outbound;get_rpc_endpoint")

    rest_cache = int(rest_cache.decode("utf-8"))
    rest_outbound = int(rest_outbound.decode("utf-8"))
    rpc_cache = int(rpc_cache.decode("utf-8"))
    rpc_outbound = int(rpc_outbound.decode("utf-8"))

    html = f"""
    <html>
        <head>
            <title>Cache Stats</title>
        </head>
        <body>
            <h1>RPC Cache Stats</h1>
            <p>RPC Cache Hits: {rpc_cache:,}</p>
            <p>RPC outbound: {rpc_outbound:,}</p>
            <p>Percent Cached: {round((rpc_cache / (rpc_cache + rpc_outbound)) * 100, 2)}%</p>
            <br>
            <h1>REST Cache Stats</h1>
            <p>REST Cache Hits: {rest_cache:,}</p>
            <p>REST outbound: {rest_outbound:,}</p>
            <p>Percent Cached: {round((rest_cache / (rest_cache + rest_outbound)) * 100, 2)}%</p>
        </body>
    </html>
    """
    return html


# return all RPC queries
@app.route("/<path:path>", methods=["GET"])
@cross_origin()
def get_all_rest(path):
    url = f"{CONFIG.REST_URL}/{path}"
    args = request.args

    cache_seconds = CONFIG.get_cache_time_seconds(path, is_rpc=False)
    if cache_seconds < 0:
        return jsonify(
            {
                "error": f"cosmos endpoint cache: The path '{path}' is disabled on this node..."
            }
        )

    key = f"{CONFIG.REST_PREFIX};{url};{args}"

    v = REDIS_DB.get(key)
    if v:
        increment_call_value("total_cache;get_all_rest")
        return jsonify(json.loads(v))

    try:
        req = requests.get(url, params=args)
    except:
        req = requests.get(f"{CONFIG.BACKUP_REST_URL}/{path}", params=args)

    if req.status_code != 200:
        return jsonify(req.json())

    REDIS_DB.setex(key, cache_seconds, json.dumps(req.json()))
    increment_call_value("total_outbound;get_all_rest")

    return req.json()


if __name__ == "__main__":
    before_first_request()
    app.run(debug=True, host="0.0.0.0", port=CONFIG.REST_PORT)
