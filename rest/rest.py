# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests
# pip install --upgrade urllib3
# ----------------------------------------------

# https://flask.palletsprojects.com/en/2.0.x/deploying/wsgi-standalone/#proxy-setups

import json
import os
from os import getenv

import redis
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

ONE_HOUR = 60 * 60
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)

load_dotenv(os.path.join(parent_dir, ".env"))

port = int(getenv("REST_PORT", 5000))


# Multiple in the future to iterate over?
# REST_URL = "https://juno-rest.reece.sh"
REST_URL = getenv("REST_URL", "https://juno-rest.reece.sh")
OPEN_API = f"{REST_URL}/static/openapi.yml"

CACHE_SECONDS = int(getenv("CACHE_SECONDS", 7))
ENABLE_COUNTER = getenv("ENABLE_COUNTER", "true").lower().startswith("t")

PREFIX = "junorest"

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


def download_openapi_locally():
    r = requests.get(OPEN_API)
    file_loc = f"{current_dir}/static/openapi.yml"
    with open(file_loc, "w") as f:
        f.write(r.text)


redis_url = getenv("CACHE_REDIS_URL", "redis://127.0.0.1:6379/0")
rDB = redis.Redis.from_url(redis_url)


total_calls = {
    "total_cache;swagger_html": 0,
    "total_cache;get_all_rest": 0,
    "total_outbound;get_all_rest": 0,
}

INC_EVERY = 25


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


# if route is just /, return the openapi swagger ui
@app.route("/", methods=["GET"])
@cross_origin()
def root():
    key = f"{PREFIX};swagger_html"
    v = rDB.get(key)
    if v:
        inc_value("total_cache;swagger_html")
        return v.decode("utf-8")

    req = requests.get(f"{REST_URL}")
    html = req.text

    rDB.setex(key, ONE_HOUR, html)

    return html


# return any RPC queries
@app.route("/<path:path>", methods=["GET"])
@cross_origin()
def get_all_rest(path):
    url = f"{REST_URL}/{path}"
    args = request.args

    key = f"{PREFIX};{url};{args}"
    v = rDB.get(key)
    if v:
        inc_value("total_cache;get_all_rest")
        return jsonify(json.loads(v.decode("utf-8")))

    try:
        req = requests.get(url, params=args)
    except:
        return {"error": "error"}

    rDB.setex(key, CACHE_SECONDS, json.dumps(req.json()))
    inc_value("total_outbound;get_all_rest")

    return req.json()


if __name__ == "__main__":
    download_openapi_locally()
    app.run(debug=True, host="0.0.0.0", port=port)
