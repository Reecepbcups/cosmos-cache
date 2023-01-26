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
