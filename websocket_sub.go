package main

import (
	"context"
	"fmt"
	"strings"
	"time"

	rpchttp "github.com/cometbft/cometbft/rpc/client/http"
)

const websocketPolling = 150 * time.Millisecond

func BlockSubscribe(cfg *Config) {
	websocketEndpoint := strings.ReplaceAll(cfg.RPC_WEBSOCKET, "/websocket", "")

	client, err := rpchttp.New(websocketEndpoint, "/websocket")
	if err != nil {
		panic(err)
	}

	err = client.Start()
	if err != nil {
		panic(err)
	}
	defer client.Stop()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	block, err := client.Subscribe(ctx, "cosmoscache-client", "tm.event = 'NewBlock'")
	if err != nil {
		panic(err)
	}

	for {
		select {
		case <-ctx.Done():
			time.Sleep(websocketPolling)
			continue
		case <-block:
			cleared := cache.ClearExpired(true)
			if cleared > 0 {
				fmt.Printf("Cache cleared %d keys.\n", cleared)
				fmt.Printf("Cache has %d remaining.\n", len(cache.Keys()))
			}
		}
	}
}
