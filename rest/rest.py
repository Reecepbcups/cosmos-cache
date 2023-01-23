# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests
# pip install --upgrade urllib3
# ----------------------------------------------

# https://flask.palletsprojects.com/en/2.0.x/deploying/wsgi-standalone/#proxy-setups

import os
from os import getenv

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_caching import Cache
from flask_cors import CORS, cross_origin

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(parent_dir, ".env"))

# Multiple in the future to iterate over?
# REST_URL = "https://juno-rest.reece.sh"
REST_URL = getenv("REST_URL", "https://juno-rest.reece.sh")
OPEN_API = f"{REST_URL}/static/openapi.yml"
port = int(getenv("REST_PORT", 5000))

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

def download_openapi_locally():
    r = requests.get(OPEN_API)
    file_loc = f"{current_dir}/static/openapi.yml"
    with open(file_loc, "w") as f:
        f.write(r.text)


download_openapi_locally()

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

# if route is just /, return the openapi swagger ui
@app.route("/", methods=["GET"])
@cross_origin()
@cache.cached(timeout=60 * 10, query_string=True)
def root():
    return requests.get(f"{REST_URL}").text


# return any RPC queries
@app.route("/<path:path>", methods=["GET"])
@cache.cached(timeout=7, query_string=True)
@cross_origin()
def get_all_rest(path):
    url = f"{REST_URL}/{path}"

    try:
        r = requests.get(url)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)
