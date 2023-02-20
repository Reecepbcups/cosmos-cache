import json
import re
from os import getenv

import httpx

import CONFIG
from CONFIG import REDIS_DB
from HELPERS_TYPES import CallType, Mode


def ttl_block_only(cache_seconds: int = 0):
    # this way on a new block, we delete all *;IsBlockOnly;* keys
    return (
        "IsBlockOnly"
        if cache_seconds == Mode.FOR_BLOCK_TIME.value
        else f"{cache_seconds}s"
    )


total_calls = {
    # RPC:
    CallType.RPC_GET_CACHE.value: 0,
    CallType.RPC_GET_OUTBOUND.value: 0,
    # RPC Post:
    CallType.RPC_POST_CACHE.value: 0,
    CallType.RPC_POST_OUTBOUND.value: 0,
    # REST:
    CallType.REST_GET_CACHE.value: 0,
    CallType.REST_GET_OUTBOUND.value: 0,
}


def increment_call_value(key: str, amount: int = 1):
    global total_calls

    if CONFIG.ENABLE_COUNTER == False:
        return

    if key not in total_calls:
        total_calls[str(key)] = 0

    if total_calls[key] >= CONFIG.INC_EVERY:
        REDIS_DB.incr(f"{key}", amount=total_calls[key])
        total_calls[key] = 0
    else:
        total_calls[key] += amount


def download_openapi_locally():
    # TODO: What if there is no swagger API?
    r = httpx.get(CONFIG.OPEN_API)
    file_loc = f"{CONFIG.PROJECT_DIR}/static/openapi.yml"
    with open(file_loc, "w") as f:
        f.write(r.text)


def get_swagger_code_from_source():
    req = httpx.get(f"{CONFIG.REST_URL}")

    html = req.text.replace(
        "//unpkg.com/swagger-ui-dist@3.40.0/favicon-16x16.png",
        "/static/favicon.png",
    )
    html = re.sub(r"<title>.*</title>", f"<title>{CONFIG.API_TITLE}</title>", html)
    return html


def replace_rpc_text() -> str:
    # we replace after on requests of the user, then replace this text to our cache endpoint at time of requests to root endpoint
    try:
        RPC_ROOT_HTML = httpx.get(f"{CONFIG.RPC_URL}/").text
    except:
        RPC_ROOT_HTML = httpx.get(f"{CONFIG.BACKUP_RPC_URL}/").text

    RPC_TITLE = getenv("RPC_TITLE", "")
    if len(RPC_TITLE) > 0:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "<html><body>",
            f"<html><head><title>{RPC_TITLE}</title></head><body>",
        )

    # Puts text at the bottom, maybe put at the top in the future?
    RPC_CUSTOM_TEXT = getenv("RPC_CUSTOM_TEXT", "")
    if len(RPC_CUSTOM_TEXT) > 0:
        RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
            "Available endpoints:<br><br>",
            f"{RPC_CUSTOM_TEXT}<br>Available endpoints:<br><br>",
        )

    # add cache_info endpoint. THIS REMOVES BLANK 'Available endpoints:<br><br>'
    RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
        "Available endpoints:<br><br>",
        f'<a href="//{{BASE_URL}}/cache_info">//{{BASE_URL}}/cache_info</a><br><br>',
        # we replace the BASE_URL on the call to the root endpoint
    )

    RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
        "/cache_info</a><br><br>",
        f'/cache_info</a><br><a href="//{{BASE_URL}}/prices">//{{BASE_URL}}/prices</a><br><br>',
        # we replace the BASE_URL on the call to the root endpoint
    )

    # Set RPC favicon to nothing
    RPC_ROOT_HTML = RPC_ROOT_HTML.replace(
        "<head>",
        f'<head><link rel="icon" href="data:,">',
    )

    return RPC_ROOT_HTML


INITIAL_HTML = """<html><head><title>Cache Stats</title></head><body>"""
CLOSING_HTML = """</body></html>"""


def get_config_values():
    KVs = [item for item in dir(CONFIG) if not item.startswith("__")]
    items = {item: getattr(CONFIG, item) for item in KVs}

    return f"""
    {INITIAL_HTML}
        <h2>Config Values</h2>        
        <p>{items}</p>
    {CLOSING_HTML}
    """


def get_stats_html():
    updates_every = CONFIG.INC_EVERY

    # gets information about the redis
    rpc_get_cache = REDIS_DB.get(CallType.RPC_GET_CACHE.value)
    rpc_get_outbound = REDIS_DB.get(CallType.RPC_GET_OUTBOUND.value)

    rpc_post_cache = REDIS_DB.get(CallType.RPC_POST_CACHE.value)
    rpc_post_outbound = REDIS_DB.get(CallType.RPC_POST_OUTBOUND.value)

    rest_cache = REDIS_DB.get(CallType.REST_GET_CACHE.value)
    rest_outbound = REDIS_DB.get(CallType.REST_GET_OUTBOUND.value)
    # no rest post yet, not added.

    # converts (1 so no div / 0 errors)
    rpc_get_cache = 1 if rpc_get_cache == None else int(rpc_get_cache.decode("utf-8"))
    rpc_get_outbound = (
        1 if rpc_get_outbound == None else int(rpc_get_outbound.decode("utf-8"))
    )

    rpc_post_cache = (
        1 if rpc_post_cache == None else int(rpc_post_cache.decode("utf-8"))
    )
    rpc_post_outbound = (
        1 if rpc_post_outbound == None else int(rpc_post_outbound.decode("utf-8"))
    )

    rest_cache = 1 if rest_cache == None else int(rest_cache.decode("utf-8"))
    rest_outbound = 1 if rest_outbound == None else int(rest_outbound.decode("utf-8"))

    return f"""
    {INITIAL_HTML}
        <h2>Updates every {updates_every} calls</h2>

        <h1>RPC GET Cache Stats</h1>
        <p>RPC Cache Hits: {rpc_get_cache}</p>
        <p>RPC outbound: {rpc_get_outbound}</p>
        <p>Percent Cached: {round((rpc_get_cache / (rpc_get_cache + rpc_get_outbound)) * 100, 2)}%</p>
        <br>
        <h1>RPC POST Cache Stats</h1>
        <p>RPC Cache Hits: {rpc_post_cache}</p>
        <p>RPC outbound: {rpc_post_outbound}</p>
        <p>Percent Cached: {round((rpc_post_cache / (rpc_post_cache + rpc_post_outbound)) * 100, 2)}%</p>
        <br>
        <h1>REST GET Cache Stats</h1>
        <p>REST Cache Hits: {rest_cache}</p>
        <p>REST outbound: {rest_outbound}</p>
        <p>Percent Cached: {round((rest_cache / (rest_cache + rest_outbound)) * 100, 2)}%</p>
    {CLOSING_HTML}
    """


def _hide_data(json: dict, str_path: str, cfg_value: str) -> dict:
    """
    cfg_value is some string
    path is the json path in string form. For example, ['result']['node_info'] is result.node_info
    json is teh default json response

    Given this, if the path exist in the json, edit said path and update it to be the cfg_value
    Then return the updated JSON

    else:
        return the original JSON
    """
    if len(str_path) == 0 or len(cfg_value) == 0:
        return json

    path = str_path.split(".")
    parent = json
    for key in path[:-1]:
        parent = parent.get(key, {})
        if not parent:
            return json
    parent[path[-1]] = cfg_value
    return json


def hide_rpc_data(res: dict, endpoint_path: str):
    if endpoint_path.lower().startswith("status"):
        res = _hide_data(res, "result.node_info.listen_addr", CONFIG.RPC_LISTEN_ADDRESS)
        res = _hide_data(
            res, "result.node_info.other.rpc_address", CONFIG.RPC_LISTEN_ADDRESS
        )
        res = _hide_data(res, "result.node_info.moniker", CONFIG.NODE_MONIKER)
        res = _hide_data(res, "result.node_info.version", CONFIG.NODE_TM_VERSION)

    return res


def hide_rest_data(res: dict, endpoint_path: str):
    if endpoint_path.lower().endswith("v1beta1/node_info"):
        res = _hide_data(
            res, "default_node_info.listen_addr", CONFIG.RPC_LISTEN_ADDRESS
        )
        res = _hide_data(
            res, "default_node_info.other.rpc_address", CONFIG.RPC_LISTEN_ADDRESS
        )
        res = _hide_data(res, "default_node_info.moniker", CONFIG.NODE_MONIKER)
        res = _hide_data(res, "default_node_info.version", CONFIG.NODE_TM_VERSION)

        # hide application_version.build_deps?

    return res
