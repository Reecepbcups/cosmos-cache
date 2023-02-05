import json
from time import time

from pycoingecko import CoinGeckoAPI

import CONFIG
from CONFIG import REDIS_DB
from HELPERS import ttl_block_only
from HELPERS_TYPES import Mode


class Coingecko:
    # https://www.coingecko.com/en/api/documentation
    # 10-30 calls per minute. So we do 6 seconds to be on the safe side by default.
    # If you use a paid plan, you can do 500+ -> https://www.coingecko.com/en/api/pricing
    def __init__(self):
        api_key = CONFIG.COINGECKO_API_KEY
        if len(api_key) > 0:
            self.cg = CoinGeckoAPI(api_key=api_key)
        else:
            self.cg = CoinGeckoAPI()

    def get_symbols(self):
        ids = CONFIG.COINGECKO_IDS

        key = f"coingecko_symbols;{ids}"
        values = REDIS_DB.get(key)
        if values is not None:
            return json.loads(values)

        values = {}
        for _id in ids:
            data = self.cg.get_coin_by_id(_id)
            symbol = data.get("symbol", "")
            values[_id] = symbol

        REDIS_DB.set(key, json.dumps(values), ex=86400)
        return values

    def get_price(self):
        ids = CONFIG.COINGECKO_IDS
        vs_currencies = CONFIG.COINGECKO_FIAT

        cache_seconds = int(CONFIG.COINGECKO_CACHE.get("seconds", 7))
        key = f"coingecko;{ttl_block_only(cache_seconds)};{ids};{vs_currencies}"

        value = REDIS_DB.get(key)
        if value is not None:
            return json.loads(value)

        symbols = self.get_symbols()  # cached 1 day
        coins = self.cg.get_price(ids=ids, vs_currencies=vs_currencies)
        # print(symbols)

        updated_coins = {}
        for k, v in coins.items():
            symbol = str(symbols.get(k, k)).upper()
            updated_coins[symbol] = {"coingecko-id": k, "prices": v}

        data = {
            "coins": updated_coins,
            "last_update": int(time()),
        }

        if cache_seconds == Mode.FOR_BLOCK_TIME.value:  # -2
            cache_seconds = int(CONFIG.DEFAULT_CACHE_SECONDS)

        REDIS_DB.set(key, json.dumps(data), ex=int(cache_seconds))
        return data


if __name__ == "__main__":
    p = Coingecko()
    # v = p.get_price()
    # print(v)

    # print(p.get_symbols())
    print(p.get_price())
