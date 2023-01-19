# Reece Williams | https://reece.sh | Jan 2023
# ----------------------------------------------
# pip install Flask redis flask_caching requests
# pip install --upgrade urllib3
# ----------------------------------------------

from os import getenv

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_caching import Cache

# Mulitple in the future to iterate over?
REST_URL = "https://juno-rest.reece.sh"
OPEN_API = f"{REST_URL}/static/openapi.yml"

load_dotenv(".env")

app = Flask(__name__)


def download_openapi_locally():
    r = requests.get(OPEN_API)
    with open("static/openapi.yml", "w") as f:
        f.write(r.text)


# run on schedule? This only updates per upgrade.
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
@cache.cached(timeout=60 * 10, query_string=True)
def root():
    return requests.get(f"{REST_URL}").text


@app.route("/<path:path>", methods=["GET"])
@cache.cached(timeout=7, query_string=True)
def get_all(path):
    url = f"{REST_URL}/{path}"

    try:
        r = requests.get(url)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
