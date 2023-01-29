import json

import httpx

import CONFIG
from CONFIG import REDIS_DB
from HELPERS import increment_call_value

timeout = httpx.Timeout(5.0, connect=5.0, read=4.0)


class RestApiHandler:
    def handle_single_rest_get_requests(
        self, path, key, cache_seconds: int, param_args
    ) -> dict:
        try:
            req = httpx.get(f"{CONFIG.REST_URL}/{path}", params=param_args)
        except:
            req = httpx.get(f"{CONFIG.BACKUP_REST_URL}/{path}", params=param_args)

        if req.status_code == 200:
            REDIS_DB.setex(key, cache_seconds, json.dumps(req.json()))
            increment_call_value("total_outbound;get_all_rest")

        return req.json()

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
        try:
            req = httpx.post(f"{CONFIG.RPC_URL}", json=REQ_DATA)
        except:
            req = httpx.post(
                f"{CONFIG.BACKUP_RPC_URL}",
                json=REQ_DATA,
            )

        if req.status_code == 200:
            # REDIS_DB.setex(key, cache_seconds, json.dumps(req.json()))
            increment_call_value("total_outbound;batch_http", len(REQ_DATA))

        return req.json()

    def handle_single_rpc_post_request(self, data, key, cache_seconds) -> dict:
        # TODO: add round robin query here for multiple RPC nodes. If a node errors, save to cache for X period to not use (unless its the only 1)
        try:
            req = httpx.post(f"{CONFIG.RPC_URL}", data=data, timeout=timeout)
        except:
            req = httpx.post(f"{CONFIG.BACKUP_RPC_URL}", data=data, timeout=timeout)

        # only saves to cache if the request was successful
        if req.status_code == 200:
            REDIS_DB.setex(key, cache_seconds, json.dumps(req.json()))
            increment_call_value("total_outbound;post_endpoint")

        return req.json()

    def handle_single_rpc_get_requests(
        self, path, key, cache_seconds: int, param_args
    ) -> dict:
        try:
            req = httpx.get(
                f"{CONFIG.RPC_URL}/{path}", params=param_args, timeout=timeout
            )
        except Exception as e:
            req = httpx.get(
                f"{CONFIG.BACKUP_RPC_URL}/{path}", params=param_args, timeout=timeout
            )

        if req.status_code == 200:
            REDIS_DB.setex(key, cache_seconds, json.dumps(req.json()))
            increment_call_value("total_outbound;get_rpc_endpoint")

        return req.json()
