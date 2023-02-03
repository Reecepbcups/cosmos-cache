import json
from time import time

from pycoingecko import CoinGeckoAPI

import CONFIG
from CONFIG import REDIS_DB


class Coingecko:
    # https://www.coingecko.com/en/api/documentation
    # 10-30 calls per minute. So we do 6 seconds to be on the safe side by default.
    # If you use a paid plan, you can do 500+ -> https://www.coingecko.com/en/api/pricing
    def __init__(self):
        self.rate_limit = CONFIG.COINGECKO_CACHE_SECONDS

        api_key = CONFIG.COINGECKO_API_KEY
        if len(api_key) > 0:
            self.cg = CoinGeckoAPI(api_key=api_key)
        else:
            self.cg = CoinGeckoAPI()

    def get_price(self):
        ids = CONFIG.COINGECKO_IDS
        vs_currencies = CONFIG.COINGECKO_FIAT

        key = f"coingecko;{ids};{vs_currencies}"
        value = REDIS_DB.get(key)
        if value is not None:
            return json.loads(value)

        data = {
            "coins": self.cg.get_price(ids=ids, vs_currencies=vs_currencies),
            "cache_seconds": self.rate_limit,
            "last_update": int(time()),
        }
        REDIS_DB.set(key, json.dumps(data), ex=self.rate_limit)
        return data


if __name__ == "__main__":
    p = Coingecko()
    v = p.get_price()
    print(v)
