from enum import Enum

import CONFIG
from CONFIG import KV_STORE


class Mode(Enum):
    NO_CACHE = 0
    DISABLED = -1
    FOR_BLOCK_TIME = -2


class CallType(Enum):
    # RPC
    RPC_GET_CACHE = f"rpc;amt;cache;rpc_get"
    RPC_GET_OUTBOUND = f"rpc;amt;outbound;rpc_get"

    # RPC POST
    RPC_POST_CACHE = f"rpc;amt;cache;rpc_post"
    RPC_POST_OUTBOUND = f"rpc;amt;outbound;rpc_post"

    # REST GET
    REST_GET_CACHE = f"rest;amt;cache;rest_get"
    REST_GET_OUTBOUND = f"rest;amt;outbound;rest_get"


if __name__ == "__main__":
    print(CallType.RPC_GET_CACHE)
    print(CallType.RPC_GET_OUTBOUND)

    print(CallType.RPC_POST_CACHE)
    print(CallType.RPC_POST_OUTBOUND)

    print(CallType.REST_GET_CACHE)
    print(CallType.REST_GET_OUTBOUND)

    v = KV_STORE.get(CallType.RPC_GET_CACHE.value)
    print(1 if v == None else int(v.decode("utf-8")))
