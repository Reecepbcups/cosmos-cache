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
    # ...
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


def replace_rpc_text() -> str:
    # Get RPC format, and replace with our domain values.
    try:
        RPC_ROOT_HTML = requests.get(f"{CONFIG.RPC_URL}/").text.replace(
            CONFIG.BASE_RPC, CONFIG.RPC_DOMAIN
        )
    except:
        RPC_ROOT_HTML = requests.get(f"{CONFIG.BACKUP_RPC_URL}/").text.replace(
            CONFIG.BACKUP_RPC_URL, CONFIG.RPC_DOMAIN
        )

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

    # add blank favicon
    if "<head>" in RPC_ROOT_HTML:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "<head>", f"<head>{CONFIG.RPC_FAVICON}", 1
        )
    else:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "<html>", f"<html><head>{CONFIG.RPC_FAVICON}</head>", 1
        )

    return RPC_ROOT_HTML
