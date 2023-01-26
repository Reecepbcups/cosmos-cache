import CONFIG
from CONFIG import rDB as REDIS_DB

print(CONFIG.PORT)
print(CONFIG.CURRENT_DIR)


print(REDIS_DB.get("junorpc;total_cache;get_rpc_endpoint"))
