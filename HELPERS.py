import re
from os import getenv

import requests

import CONFIG
from CONFIG import REDIS_DB

total_calls = {
    # RPC:
    "total_cache;get_rpc_endpoint": 0,
    "total_outbound;get_rpc_endpoint": 0,
    # RPC Cache:
    "total_cache;post_endpoint": 0,
    "total_outbound;post_endpoint": 0,
    # REST:
    "total_cache;get_all_rest": 0,
    "total_outbound;get_all_rest": 0,
}


def increment_call_value(key):
    global total_calls

    if CONFIG.ENABLE_COUNTER == False:
        return

    if key not in total_calls:
        total_calls[key] = 0

    if total_calls[key] >= CONFIG.INC_EVERY:
        REDIS_DB.incr(f"{CONFIG.RPC_PREFIX};{key}", amount=total_calls[key])
        total_calls[key] = 0
    else:
        total_calls[key] += 1


def download_openapi_locally():
    r = requests.get(CONFIG.OPEN_API)
    file_loc = f"{CONFIG.CURRENT_DIR}/static/openapi.yml"
    with open(file_loc, "w") as f:
        f.write(r.text)


def get_swagger_code_from_source():
    req = requests.get(f"{CONFIG.REST_URL}")

    html = req.text.replace(
        "//unpkg.com/swagger-ui-dist@3.40.0/favicon-16x16.png",
        "/static/rest-favicon.png",
    )
    html = re.sub(r"<title>.*</title>", f"<title>{CONFIG.API_TITLE}</title>", html)
    return html


def replace_rpc_text() -> str:
    # we replace after on requests of the user, then repalce this text to our cache endpoint at time of requests to root endpoint
    try:
        RPC_ROOT_HTML = requests.get(f"{CONFIG.RPC_URL}/").text
    except:
        RPC_ROOT_HTML = requests.get(f"{CONFIG.BACKUP_RPC_URL}/").text

    RPC_TITLE = getenv("RPC_TITLE", "")
    if len(RPC_TITLE) > 0:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "<html><body>",
            f"<html><head><title>{RPC_TITLE}</title></head><body>",
        )

    # Puts text at the bottom, maybe put at the top in the future?
    RPC_CUSTOM_TEXT = getenv("RPC_CUSTOM_TEXT", "").replace(
        "{RPC_DOMAIN}", f"{CONFIG.RPC_DOMAIN}"
    )
    if len(RPC_CUSTOM_TEXT) > 0:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "Available endpoints:<br><br>",
            f"{RPC_CUSTOM_TEXT}<br>Available endpoints:<br><br>",
        )

    # add cache_info endpoint. THIS REMOVES BLANK Available endpoints:<br><br>
    RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
        "Available endpoints:<br><br>",
        f'<a href="//{CONFIG.RPC_DOMAIN}/cache_info">Cache Information</a><br><br>',
    )

    # Set RPC favicon to nothing
    RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
        "<head>",
        f'<head><link rel="icon" href="data:,">',
    )

    return RPC_ROOT_HTML
