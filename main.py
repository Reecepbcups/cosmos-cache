# https://levelup.gitconnected.com/implement-api-caching-with-redis-flask-and-docker-step-by-step-9139636cef24


from os import getenv

# pip install Flask redis flask_caching requests
# pip install --upgrade urllib3
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_caching import Cache

load_dotenv(".env")

app = Flask(__name__)

# juno10r39fueph9fq7a6lgswu4zdsg8t3gxlq670lt0

REST_URL = "https://juno-rest.reece.sh"
OPEN_API = f"{REST_URL}/static/openapi.yml"


def download_open_api_locally():
    r = requests.get(OPEN_API)
    with open("static/openapi.yml", "w") as f:
        f.write(r.text)


# run on schedule?
download_open_api_locally()

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

# if route is just /, return the openapi.yml
@app.route("/", methods=["GET"])
@cache.cached(timeout=6, query_string=True)
def root():
    return requests.get(f"{REST_URL}").text


@app.route("/<path:path>", methods=["GET"])
@cache.cached(timeout=6, query_string=True)
def get_all(path):
    url = f"{REST_URL}/{path}"

    # do the above with a list
    if any(x in path for x in ["/params", "/proposals"]):
        cache.cached(timeout=60 * 5, query_string=True)

    r = requests.get(url)
    return jsonify(r.json())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
