# Akash

**NOTE** At the moment, you can not use multiple workers without compiling the docker image yourself. In the future, I would like to find a way to make this variable. By default, it is 1 worker and 1 thread in the WSGI server.

You can utilize Akash to deploy your application to the decentralized cloud for cheaper than AWS, GCP, etc. This document will outline considerations you need to account for when deploying infrastructure.

> [Deploy Tool](https://deploy.cloudmos.io/)

---

# Setup

You can find the deploy.yaml file [here](../akash/deploy.yaml). This file does not require the `"` string to prefix in the environment variables. Open this file in the [Cloudmos deploy tool](https://deploy.cloudmos.io/).
After running, you must edit the `deploy.yaml` file to to your needs. For now, leave the redis url lines default (currently localhost Redis connections do not work for some reason)

Be sure to update the `REMOTE_CONFIG_TIME_FILE` env variable for your needs. The default configuration is to only keep data for the length of the block, then wipe it if you have the Websocket RPC set. If not, it will default to 6 seconds of time to live. This means at max your data is 5 seconds old on most Tendermint chains. Even so, we recomend you use -2 for this option. To see other options, review the [Config Values](./CONFIG_VALUES.md) file.

After uploading and deploying to a provider, your instances will fail. To solve this, we must now update to the user URI and forwarded ports from the provider. This is found in the `Leases` page in the deploy tool online. It will look something like this `http://l94r5hl2itcct9f1vpkd88fno4.ingress.palmito.duckdns.org/` and forwarded ports like so `6379:31652` for example.

Take the URI and Redis URL forwarded port, then put it in the config by clicking on the `update` tag in the deploy tool. This is how it will look:

```bash
  ...

  env:
    REDIS_URL=redis://l94r5hl2itcct9f1vpkd88fn04.ingress.palmito.duckdns.org:31622/0
    ...
  # NOTE: if you click on the forwarded ports link, it will return a cleaner URL like so:
  # provider.palmito.duckdns.org:31622
```

Then press the `update deployment` button on the right-hand side of the screen, and approve the transaction. Once this has been completed, you can use the cache as intended.
