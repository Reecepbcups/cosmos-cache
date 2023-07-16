package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
	"time"

	rpchttp "github.com/cometbft/cometbft/rpc/client/http"
)

const (
	websocketPolling = 100 * time.Millisecond
)

var (
	// Set in ctx instead?
	HTMLCache           = ""
	OpenAPISwaggerCache = ""

	// TODO: Get this on first request to / and then parse and save it? (tm 37 support?)
	rpcEndpointsTM34 = map[string]bool{
		"/":                     true,
		"/abci_info":            true,
		"/abci_query":           true,
		"/block":                true,
		"/block_by_hash":        true,
		"/block_results":        true,
		"/block_search":         true,
		"/blockchain":           true,
		"/broadcast_evidence":   true,
		"/broadcast_tx_async":   true,
		"/broadcast_tx_commit":  true,
		"/broadcast_tx_sync":    true,
		"/check_tx":             true,
		"/commit":               true,
		"/consensus_params":     true,
		"/consensus_state":      true,
		"/dump_consensus_state": true,
		"/genesis":              true,
		"/genesis_chunked":      true,
		"/health":               true,
		"/net_info":             true,
		"/num_unconfirmed_txs":  true,
		"/status":               true,
		"/subscribe":            true,
		"/tx":                   true,
		"/tx_search":            true,
		"/unconfirmed_txs":      true,
		"/unsubscribe":          true,
		"/unsubscribe_all":      true,
		"/validators":           true,
		// This is done at the Reverse-Proxy level for now.
		"/websocket": true,
	}

	DefaultCacheTimeSeconds = 6

	cache = Cache{
		Store: make(map[string]CacheValue),
	}

	// TODO: Status codes
	stats = make(map[string]int)
)

func blockSubscribe(cfg *Config) {
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

func rpcHtmlView(w http.ResponseWriter, r *http.Request, cfg *Config, body string) []byte {
	w.Header().Set("Content-Type", "text/html")

	baseRpc := strings.ReplaceAll(cfg.RPC, "http://", "")
	baseRpc = strings.ReplaceAll(baseRpc, "https://", "")
	base := strings.ReplaceAll(body, baseRpc, r.Host)

	coingeckoURL := fmt.Sprintf("Coingecko Asset Prices:<br><a href=//%s/prices>//%s/prices</a><br>", r.Host, r.Host)
	if cfg.COINGECKO_ENABLED {
		base = strings.ReplaceAll(base, "Available endpoints:<br>", coingeckoURL)
	}

	if cfg.RPC_TITLE != "" {
		title := fmt.Sprintf("<html><title>%s</title>", cfg.RPC_TITLE)
		base = strings.ReplaceAll(base, "<html>", title)
	}

	if cfg.RPC_CUSTOM_TEXT != "" {
		base = strings.ReplaceAll(base, "<body>", fmt.Sprintf("<body>%s", cfg.RPC_CUSTOM_TEXT))
	}

	// TODO: This is hidden if coingecko is not set. Set a private comment / unseen list or something?
	apiURL := fmt.Sprintf("%s<br>REST API:<br><a href=//%s/api>//%s/api</a><br>", coingeckoURL, r.Host, r.Host)
	if cfg.REST_URL != "" {
		base = strings.ReplaceAll(base, coingeckoURL, apiURL)
	}

	return []byte(base)
}

func hideStatusValues(cfg *Config, body []byte) []byte {
	// RPC/status
	type Status struct {
		Jsonrpc string `json:"jsonrpc"`
		ID      int    `json:"id"`
		Result  struct {
			NodeInfo struct {
				ProtocolVersion struct {
					P2P   string `json:"p2p"`
					Block string `json:"block"`
					App   string `json:"app"`
				} `json:"protocol_version"`
				ID         string `json:"id"`
				ListenAddr string `json:"listen_addr"`
				Network    string `json:"network"`
				Version    string `json:"version"`
				Channels   string `json:"channels"`
				Moniker    string `json:"moniker"`
				Other      struct {
					TxIndex    string `json:"tx_index"`
					RPCAddress string `json:"rpc_address"`
				} `json:"other"`
			} `json:"node_info"`
			SyncInfo struct {
				LatestBlockHash     string    `json:"latest_block_hash"`
				LatestAppHash       string    `json:"latest_app_hash"`
				LatestBlockHeight   string    `json:"latest_block_height"`
				LatestBlockTime     time.Time `json:"latest_block_time"`
				EarliestBlockHash   string    `json:"earliest_block_hash"`
				EarliestAppHash     string    `json:"earliest_app_hash"`
				EarliestBlockHeight string    `json:"earliest_block_height"`
				EarliestBlockTime   time.Time `json:"earliest_block_time"`
				CatchingUp          bool      `json:"catching_up"`
			} `json:"sync_info"`
			ValidatorInfo struct {
				Address string `json:"address"`
				PubKey  struct {
					Type  string `json:"type"`
					Value string `json:"value"`
				} `json:"pub_key"`
				VotingPower string `json:"voting_power"`
			} `json:"validator_info"`
			MevInfo struct {
				IsPeeredWithSentinel     bool   `json:"is_peered_with_sentinel"`
				LastReceivedBundleHeight string `json:"last_received_bundle_height"`
			} `json:"mev_info"`
		} `json:"result"`
	}

	var status Status
	err := json.Unmarshal(body, &status)
	if err != nil {
		log.Fatal(err)
	}

	status.Result.NodeInfo.ListenAddr = cfg.RPC_LISTEN_ADDRESS
	status.Result.NodeInfo.Other.RPCAddress = cfg.RPC_LISTEN_ADDRESS

	status.Result.NodeInfo.Moniker = cfg.NODE_MONIKER
	status.Result.NodeInfo.Version = cfg.NODE_TM_VERSION

	// validator_info?

	// convert back to string
	bz, err := json.Marshal(status)
	if err != nil {
		log.Fatal(err)
	}

	return bz
}

func HandleRequest(w http.ResponseWriter, r *http.Request, endpoint string, cfg *Config, cache Cache) {
	// if request is for /, then show the html view
	if r.URL.Path == "/" && HTMLCache != "" && endpoint == cfg.RPC {
		// fmt.Println("HTML Cache hit")
		stats["HTML_CACHE"]++
		w.Header().Set("Content-Type", "text/html")

		fmt.Fprint(w, HTMLCache)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	fullPath := r.URL.Path + "?" + r.URL.Query().Encode()
	url := endpoint + fullPath

	timeout := cfg.GetTimeout(fullPath)
	if timeout == -1 {
		fmt.Fprintf(w, `{"error":"This endpoint '%s' is disabled."}`, r.URL.Path)
		return
	}

	if res := cache.Get(url); res != nil {
		fmt.Println("Cache hit")
		stats["CACHE_"+endpoint]++
		fmt.Fprint(w, res.Value)
		return
	}

	res, err := http.Get(url)
	if err != nil {
		log.Fatal(err)
	}

	body, err := ioutil.ReadAll(res.Body)
	if err != nil {
		log.Fatal(err)
	}

	if strings.HasPrefix(string(body), "<html>") {
		body = rpcHtmlView(w, r, cfg, string(body))

		HTMLCache = string(body)
		fmt.Fprint(w, HTMLCache)
		return
	}

	// if path starts with /status, then we need to replace some of the data
	if endpoint == cfg.RPC && strings.HasPrefix(r.URL.Path, "/status") {
		body = hideStatusValues(cfg, body)
	}

	cache.Set(url, string(body), timeout)

	stats[endpoint]++
	fmt.Fprint(w, string(body))
}

func main() {
	cfg := LoadConfigFromFile(".env")
	cfg.LoadCacheTimes("cache_times.json")

	httpClient := http.Client{
		Timeout: time.Second * 10,
	}

	server := NewServer(httpClient, cfg, &cache)

	endpoint := cfg.APP_HOST + ":" + cfg.APP_PORT
	// TODO: Start Flags options
	go blockSubscribe(cfg)

	server.Start(endpoint)
}
