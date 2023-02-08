import json

import httpx

import CONFIG
from CONFIG import REDIS_DB
from HELPERS import hide_rest_data, hide_rpc_data, increment_call_value
from HELPERS_TYPES import CallType, Mode

timeout = httpx.Timeout(30.0, connect=5.0, read=4.0)


def set_cache_for_time_if_valid(
    status_code: int,
    call_key: str,
    cache_seconds: int,
    redis_key: str,
    res: dict,
    use_hset: bool = False,
    second_key: str = "",
):

    if status_code == 200:
        increment_call_value(call_key)

        if cache_seconds == Mode.FOR_BLOCK_TIME.value:  # -2
            if CONFIG.DEFAULT_CACHE_SECONDS > 0:
                cache_seconds = CONFIG.DEFAULT_CACHE_SECONDS
            else:
                cache_seconds = 6

        if cache_seconds > 0:
            if use_hset:
                # expires the entire hset at some period of time
                REDIS_DB.hset(redis_key, second_key, json.dumps(res))
                REDIS_DB.expire(redis_key, cache_seconds)
            else:
                REDIS_DB.setex(redis_key, cache_seconds, json.dumps(res))


class RestApiHandler:
    def handle_single_rest_get_requests(
        self, path, key, cache_seconds: int, param_args
    ) -> dict:
        try:
            req = httpx.get(f"{CONFIG.REST_URL}/{path}", params=param_args)
        except:
            req = httpx.get(f"{CONFIG.BACKUP_REST_URL}/{path}", params=param_args)

        res = hide_rest_data(req.json(), path)

        set_cache_for_time_if_valid(
            req.status_code, CallType.REST_GET_OUTBOUND.value, cache_seconds, key, res
        )

        return res

    # This breaks right now, very few ever will do this. Needs to be done in the future though, but not a priority
    # def handle_single_rest_post_requests(self, path, data: dict) -> dict:
    #     # simulate, txs
    #     try:
    #         req = httpx.post(
    #             f"{CONFIG.RPC_URL}/{path}", headers=CONFIG.HEADERS, data=data
    #         )
    #     except:
    #         req = httpx.post(
    #             f"{CONFIG.BACKUP_RPC_URL}/{path}",
    #             headers=CONFIG.HEADERS,
    #             data=data,
    #         )
    #     return req.json()


class RPCHandler:
    def handle_batch_http_request(self, REQ_DATA: list) -> dict:
        """
        This function handles batch http requests from TendermintClient34.create client
        """
        # TODO: add cache here in the future possible? since each elem in the list has a method and params like below
        # TODO: add hide_rpc_data here for each if they req the status method
        try:
            req = httpx.post(f"{CONFIG.RPC_URL}", json=REQ_DATA)
        except:
            req = httpx.post(
                f"{CONFIG.BACKUP_RPC_URL}",
                json=REQ_DATA,
            )

        return req.json()

    def handle_single_rpc_post_request(
        self, data, key, method, cache_seconds, use_hset: bool = False
    ) -> dict:
        # TODO: add round robin query here for multiple RPC nodes. If a node errors, save to cache for X period to not use (unless its the only 1)
        try:
            req = httpx.post(f"{CONFIG.RPC_URL}", data=data, timeout=timeout)
        except:
            req = httpx.post(f"{CONFIG.BACKUP_RPC_URL}", data=data, timeout=timeout)

        # only saves to cache if the request was successful
        res = hide_rpc_data(req.json(), method)

        set_cache_for_time_if_valid(
            req.status_code,
            CallType.RPC_POST_OUTBOUND.value,
            cache_seconds,
            key,
            res,
            use_hset,
            second_key=str(data),
        )

        return res

    def handle_single_rpc_get_requests(
        self, path, key, param_args, cache_seconds: int, use_hset: bool = False
    ) -> dict:
        try:
            req = httpx.get(
                f"{CONFIG.RPC_URL}/{path}", params=param_args, timeout=timeout
            )
        except Exception as e:
            req = httpx.get(
                f"{CONFIG.BACKUP_RPC_URL}/{path}", params=param_args, timeout=timeout
            )

        res = hide_rpc_data(req.json(), path)

        set_cache_for_time_if_valid(
            req.status_code,
            CallType.RPC_GET_OUTBOUND.value,
            cache_seconds,
            key,
            res,
            use_hset,
            second_key=str(param_args),
        )

        return res
