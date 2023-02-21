import json
import os
import re
from os import getenv

import redis
import requests
from dotenv import load_dotenv

HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
}

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

env_file = os.path.join(PROJECT_DIR, ".env")


load_dotenv(env_file)
USE_BACKUP_AS_PRIMARY = getenv("USE_BACKUP_AS_PRIMARY", "false").lower().startswith("t")

## == Helper == ##
REMOTE_CONFIG_TIME_FILE = getenv("REMOTE_CONFIG_TIME_FILE", "")
if not os.path.exists(env_file):
    if len(REMOTE_CONFIG_TIME_FILE) == 0:
        # error as we are not using docker
        print("No .env file found. Please copy it and edit. `cp configs/.env .env`")
        exit(1)


def get_config_file(filename: str):
    """
    Gets the custom config file if it exist. If not, uses the custom one if allowed.

    If it is the cache time, we allow it to be downloaded from a remote source so that docker/akash is easier to use
    """
    if filename == "cache_times.json" and len(REMOTE_CONFIG_TIME_FILE) > 0:
        if os.path.exists(filename):
            return os.path.join(PROJECT_DIR, filename)
        else:
            print("Downloading remote config file...")
            r = requests.get(REMOTE_CONFIG_TIME_FILE).text
            with open(os.path.join(PROJECT_DIR, filename), "w") as f:
                f.write(r)

    # custom file if they moved to the project root dir
    custom_config = os.path.join(PROJECT_DIR, filename)
    if os.path.exists(custom_config):
        return custom_config

    return os.path.join(PROJECT_DIR, "configs", filename)  # default


# =============
# === REDIS ===
# =============
REDIS_URL = getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

if "http://" in REDIS_URL or "https://" in REDIS_URL:
    # remove that http from the url
    REDIS_URL = REDIS_URL.replace("http://", "").replace("https://", "")
    print(
        "WARNING: Found http(s):// in your URL. It has been removed but you should ensure this is correct."
    )

REDIS_DB = redis.Redis.from_url(REDIS_URL)


redis_config = get_config_file("redis.json")
values = json.loads(open(redis_config, "r").read()).items()
if len(values) > 0:
    for k, v in values:
        REDIS_DB.config_set(k, v)


ENABLE_COUNTER = getenv("ENABLE_COUNTER", "true").lower().startswith("t")
INC_EVERY = int(getenv("INCREASE_COUNTER_EVERY", 250))
STATS_PASSWORD = getenv("STATS_PASSWORD", "")

# === Coingecko ===
COINGECKO_ENABLED = getenv("COINGECKO_ENABLED", "true").lower().startswith("t")
COINGECKO_API_KEY = getenv("COINGECKO_API_KEY", "")
COINGECKO_IDS = getenv("COINGECKO_IDS", "cosmos,juno-network,osmosis").split(",")
COINGECKO_FIAT = getenv("COINGECKO_FIAT", "usd,eur").split(",")

# ===========
# === RPC ===
# ===========
RPC_PORT = int(getenv("RPC_PORT", 5001))
RPC_PREFIX = getenv("REDIS_RPC_PREFIX", "junorpc")


RPC_URL = getenv("RPC_URL", "https://juno-rpc.reece.sh:443")
BACKUP_RPC_URL = getenv("BACKUP_RPC_URL", "https://rpc.juno.strange.love:443")
if USE_BACKUP_AS_PRIMARY:
    RPC_URL = BACKUP_RPC_URL

RPC_WEBSOCKET = getenv("RPC_WEBSOCKET", "ws://15.204.143.232:26657/websocket")
BACKUP_RPC_WEBSOCKET = getenv(
    "BACKUP_RPC_WEBSOCKET", "ws://rpc.juno.strange.love:443/websocket"
)
if USE_BACKUP_AS_PRIMARY:
    RPC_WEBSOCKET = BACKUP_RPC_WEBSOCKET

# ============
# === REST ===
# ============
REST_PORT = int(getenv("REST_PORT", 5000))

API_TITLE = getenv("API_TITLE", "Swagger API")
REST_PREFIX = getenv("REDIS_REST_PREFIX", "junorest")

REST_URL = getenv("REST_URL", "https://juno-rest.reece.sh")
BACKUP_REST_URL = getenv("BACKUP_REST_URL", f"https://api.juno.strange.love")
if USE_BACKUP_AS_PRIMARY:
    REST_URL = BACKUP_REST_URL

OPEN_API = f"{REST_URL}/static/openapi.yml"

DISABLE_SWAGGER_UI = getenv("DISABLE_SWAGGER_UI", "false").lower().startswith("t")

# Security
RPC_LISTEN_ADDRESS = getenv("RPC_LISTEN_ADDRESS", "")
NODE_MONIKER = getenv("NODE_MONIKER", "")
NODE_TM_VERSION = getenv("NODE_TM_VERSION", "")

# === Cache Times ===
DEFAULT_CACHE_SECONDS: int = 6

cache_times: dict = {}
RPC_ENDPOINTS: dict = {}
REST_ENDPOINTS: dict = {}
COINGECKO_CACHE: dict = {}

# === CACHE HELPER ===
def update_cache_times():
    """
    Updates any config variables which can be changed without restarting the server.
    Useful for the /cache_info endpoint & actually applying said cache changes at any time
    """
    global cache_times, DEFAULT_CACHE_SECONDS, RPC_ENDPOINTS, REST_ENDPOINTS, COINGECKO_CACHE

    cache_times_config = get_config_file("cache_times.json")
    cache_times = json.loads(open(cache_times_config, "r").read())

    DEFAULT_CACHE_SECONDS = cache_times.get("DEFAULT", 6)
    RPC_ENDPOINTS = cache_times.get("rpc", {})
    REST_ENDPOINTS = cache_times.get("rest", {})
    COINGECKO_CACHE = cache_times.get("coingecko", {})


def get_cache_time_seconds(path: str, is_rpc: bool) -> int:
    """
    Returns an endpoints time to cache in seconds
    """
    endpoints = RPC_ENDPOINTS if is_rpc else REST_ENDPOINTS

    cache_seconds = DEFAULT_CACHE_SECONDS
    for k, seconds in endpoints.items():
        if re.match(k, path):
            cache_seconds = seconds
            break

    return cache_seconds
