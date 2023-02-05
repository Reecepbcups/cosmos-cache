# Documentation

This section contains information about different configuration files used by this program.

## Workers vs Threads

This program uses a combination of workers and threads to handle the requests. Increase the number of threads greater than workers to handle more throughput requests.
Ideally, you should set this to = `(CPUS/2) * (THREADS*2)`. Though you may find that `(CPU/4) * (THREADS*4)` is more optimal. More threads are better.

## .env

For the best performance, disabled the counter and/or increase the interval to a high number (say 10,000) like so. By doing this, it will drastically reduce the number of logging increment requests to the Redis server instance. (So every query, then adds +1 in memory. Then dumps to Redis at call 10,000 in a single incr(10000) call to be most efficient)

```env
# == QUERY INCREMENT LOGGING ===
ENABLE_COUNTER=false
INCREASE_COUNTER_EVERY=10000
```

---

## Variable Length Cache

In the `cache_times.json` file, you can specify specific endpoints and how long said queries should persist in the cache.
This is useful for large queries such as /validators which may return 100+ validators. This data does not change often, making it useful for caching for longer periods.

There are 4 options:

- > -2: Cache for the duration of the block (Subscribes to RPC_WEBSOCKET in .env file)
- > -1: Disable this query entirely (prevent DoS attacks on the node)
- >  0: No cache
- > 1+: Cache for the specified number of seconds

This file uses regex pattern matching as keys, with values as the number of seconds to cache once it has been called.
For python strings, you must prefix any `*` you find with a `.` (period). So to match "random" in "my 8 random11 string", you would do `.*random.*` to match all before and after.
