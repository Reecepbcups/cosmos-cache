# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests
# pip install --upgrade urllib3
# ----------------------------------------------

# https://flask.palletsprojects.com/en/2.0.x/deploying/wsgi-standalone/#proxy-setups

import json
import os
import re
from os import getenv

import redis
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)

# Load specific cache times (regex supported)
with open(f"{parent_dir}/cache_times.json", "r") as f:
    cache_times: dict = json.loads(f.read())

DEFAULT_CACHE_SECONDS = cache_times.get("DEFAULT", 6)
ENDPOINTS = cache_times.get("rest", {})

load_dotenv(os.path.join(parent_dir, ".env"))

API_TITLE = getenv("API_TITLE", "Swagger API")

port = int(getenv("REST_PORT", 5000))

# Multiple in the future to iterate over?
# REST_URL = "https://juno-rest.reece.sh"
REST_URL = getenv("REST_URL", "https://juno-rest.reece.sh")
OPEN_API = f"{REST_URL}/static/openapi.yml"


ENABLE_COUNTER = getenv("ENABLE_COUNTER", "true").lower().startswith("t")

PREFIX = getenv("REDIS_REST_PREFIX", "junorest")

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


def download_openapi_locally():
    r = requests.get(OPEN_API)
    file_loc = f"{current_dir}/static/openapi.yml"
    with open(file_loc, "w") as f:
        f.write(r.text)


REDIS_URL = getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
rDB = redis.Redis.from_url(REDIS_URL)


total_calls = {
    "total_cache;get_all_rest": 0,
    "total_outbound;get_all_rest": 0,
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


HTML = ""

# if route is just /, return the openapi swagger ui
@app.route("/", methods=["GET"])
@cross_origin()
def root():
    global HTML

    if len(HTML) > 0:
        return HTML

    # sets HTML if not set
    req = requests.get(f"{REST_URL}")

    HTML = req.text.replace(
        "//unpkg.com/swagger-ui-dist@3.40.0/favicon-16x16.png", "/static/favicon.png"
    )
    HTML = re.sub(r"<title>.*</title>", f"<title>{API_TITLE}</title>", HTML)

    return HTML


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

    # Sets special endpoints to cache for longer/ shorter as needed
    cache_seconds = next(
        (v for k, v in ENDPOINTS.items() if re.match(k, path)), DEFAULT_CACHE_SECONDS
    )

    rDB.setex(key, cache_seconds, json.dumps(req.json()))
    inc_value("total_outbound;get_all_rest")

    return req.json()


if __name__ == "__main__":
    download_openapi_locally()
    app.run(debug=True, host="0.0.0.0", port=port)
