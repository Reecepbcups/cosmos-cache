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

## Variable Length Cache

In the `cache_times.json` file, you can specify specific endpoints and how long said queries should persist in the cache.
This is useful for large queries such as /validators which may return 100+ validators. This data does not change often, making it useful for caching for longer periods.

If you wish to disable the cache, you can set the value to 0 for the said endpoint. If you wish to disable the endpoint query entirely, set it to a value less than 0 (such as -1).
By default, the cosmos/auth/v1beta1/accounts endpoint is disabled, as it temporarily halts the node.

This file uses regex pattern matching as keys, with values as the number of seconds to cache once it has been called.
For python strings, you must prefix any `*` you find with a `.`. So to match "random" in "my 8 random11 string", you would do `.*random.*` to match all before and after.

This is ONLY the path, which means it does not start with a `/`.
