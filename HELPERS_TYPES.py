from enum import Enum

import CONFIG
from CONFIG import REDIS_DB


class Mode(Enum):
    NO_CACHE = 0
    DISABLED = -1
    FOR_BLOCK_TIME = -2


class CallType(Enum):
    # RPC
    RPC_GET_CACHE = f"{CONFIG.RPC_PREFIX};amt;cache;rpc_get"
    RPC_GET_OUTBOUND = f"{CONFIG.RPC_PREFIX};amt;outbound;rpc_get"

    # RPC POST
    RPC_POST_CACHE = f"{CONFIG.RPC_PREFIX};amt;cache;rpc_post"
    RPC_POST_OUTBOUND = f"{CONFIG.RPC_PREFIX};amt;outbound;rpc_post"

    # REST GET
    REST_GET_CACHE = f"{CONFIG.REST_PREFIX};amt;cache;rest_get"
    REST_GET_OUTBOUND = f"{CONFIG.REST_PREFIX};amt;outbound;rest_get"


if __name__ == "__main__":
    print(CallType.RPC_GET_CACHE)
    print(CallType.RPC_GET_OUTBOUND)

    print(CallType.RPC_POST_CACHE)
    print(CallType.RPC_POST_OUTBOUND)

    print(CallType.REST_GET_CACHE)
    print(CallType.REST_GET_OUTBOUND)

    v = REDIS_DB.get(CallType.RPC_GET_CACHE.value)
    print(1 if v == None else int(v.decode("utf-8")))
