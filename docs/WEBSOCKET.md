# Tendermint WebSocket

In Cosmos, some application use Tendermint's websocket to subscribe to events (Specifically keplr to check for when a Tx has completed in their UI). The following is an example for how to add WebSocket support to your cached RPC via NGINX. 

## NGINX Config

```conf
http {    
    upstream juno_rpc_cache {
        server 11.123.123.123:5001;
    }

    upstream juno-ws-backend {
        ip_hash;
        # Juno direct RPC address
        server 11.123.123.123:26657;
    }

    # ...
    
    server {
        listen 80;
        server_name juno-rpc.reece.sh;  

        # websocket connections only
        # (We convert wss to ws so we do not have to deal with certificates)
        location /websocket {            
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            
            proxy_pass http://juno-ws-backend/websocket;

            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # every other requests through juno-rpc.reece.sh goes here to the standard RPC
        location / {
            add_header Access-Control-Max-Age 3600;
            add_header Access-Control-Expose-Headers Content-Length;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header X-NginX-Proxy true;

            add_header Referrer-Policy 'origin';
            
            proxy_pass http://juno_rpc_cache;

            # WebSocket support            
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }        
    }
}

```

## Caddy Config

- TODO