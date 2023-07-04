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

	"github.com/gorilla/mux"

	rpchttp "github.com/cometbft/cometbft/rpc/client/http"
)

const (
	rpc                     = "https://rpc.juno.strange.love"
	api                     = "https://api.juno.strange.love"
	websocketUrl, websocket = "https://rpc.juno.strange.love:443", "/websocket"

	websocketPolling = 100 * time.Millisecond
)

var (
	// Set in ctx instead?
	HTMLCache           = ""
	OpenAPISwaggerCache = ""

	// TODO: Get this on first request to / and then parse and save it? (tm 37 support?)
	rpcEndpoints = map[string]bool{
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
		"/websocket":            true,
	}

	DefaultCacheTimeSeconds = 6

	cache = Cache{
		Store: make(map[string]CacheValue),
	}

	// TODO: Status codes
	stats = make(map[string]int)
)

func blockSubscribe() {
	client, err := rpchttp.New(websocketUrl, websocket)
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

	baseRpc := strings.ReplaceAll(rpc, "http://", "")
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

	apiURL := fmt.Sprintf("%s<br>REST API:<br><a href=//%s/api>//%s/api</a><br>", coingeckoURL, r.Host, r.Host)
	if cfg.REST_URL != "" {
		base = strings.ReplaceAll(base, coingeckoURL, apiURL)
	}

	return []byte(base)
}

func HandleRequest(w http.ResponseWriter, r *http.Request, endpoint string, cfg *Config, cache Cache) {
	// if request is for /, then show the html view
	if r.URL.Path == "/" && HTMLCache != "" && endpoint == rpc {
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
	// fmt.Println("Timeout of", timeout)
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
		return
	}

	cache.Set(url, string(body), timeout)

	stats[endpoint]++
	fmt.Fprint(w, string(body))
}

func main() {
	cfg := LoadConfigFromFile(".env")
	cfg.LoadCacheTimes("cache_times.json")

	r := mux.NewRouter()

	go blockSubscribe()

	httpClient := &http.Client{
		Timeout: time.Second * 10,
	}

	// panic | crash
	r.HandleFunc("/panic", func(w http.ResponseWriter, r *http.Request) {
		panic("Panic!")
	})

	r.HandleFunc("/favicon.ico", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "image/x-icon")

		if res := cache.Get("favicon.ico"); res != nil {
			fmt.Println("Favicon cache hit")
			stats["CACHE_favicon"]++
			fmt.Fprint(w, res.Value)
			return
		}

		body, err := ioutil.ReadFile("static/favicon.png")
		if err != nil {
			log.Fatal(err)
		}

		cache.Set("favicon.ico", string(body), int(30*time.Minute.Seconds()))
		fmt.Fprint(w, string(body))
	})

	r.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		statsJson, err := json.Marshal(stats)
		if err != nil {
			log.Fatal(err)
		}

		fmt.Fprint(w, string(statsJson))
	})

	r.HandleFunc("/prices", func(w http.ResponseWriter, r *http.Request) {
		if !cfg.COINGECKO_ENABLED {
			fmt.Fprint(w, "Coingecko not enabled on this node.")
			return
		}
		w.Header().Set("Content-Type", "application/json")

		prices := CoingeckoQuery(httpClient, cfg.COINGECKO_IDS, cfg.COINGECKO_FIAT)
		pricesJson, err := json.Marshal(prices)
		if err != nil {
			log.Fatal(err)
		}

		stats["prices"]++

		fmt.Fprint(w, string(pricesJson))
	})

	// if route is static/openapi.yml, then show the swagger api
	r.HandleFunc("/static/openapi.yml", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("OpenAPI cache hit")

		w.Header().Set("Content-Type", "text/html")

		if len(OpenAPISwaggerCache) > 0 {
			stats["open_api_cache"]++
			fmt.Fprint(w, OpenAPISwaggerCache)
			return
		}

		body, err := ioutil.ReadFile("static/openapi.yml")
		if err != nil {
			log.Fatal(err)
		}

		stats["open_api"]++

		OpenAPISwaggerCache = string(body)
		fmt.Fprint(w, OpenAPISwaggerCache)
	})

	// handle func for any route / wildcard
	r.HandleFunc("/{route:.*}", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api" || r.URL.Path == "/swagger" {
			stats["rest_api"]++
			fmt.Println("REST API hit")
			// get api as http get
			w.Header().Set("Content-Type", "text/html")
			res, err := http.Get(api)
			if err != nil {
				log.Fatal(err)
			}

			body, err := ioutil.ReadAll(res.Body)
			if err != nil {
				log.Fatal(err)
			}

			// Set Swagger title.
			if cfg.API_TITLE != "" {
				// TODO: If swagger is disabled, then do a different replace.
				for _, line := range strings.Split(string(body), "\n") {
					if strings.Contains(line, "<title>") {
						body = []byte(strings.ReplaceAll(string(body), line, fmt.Sprintf("<title>%s</title>", cfg.API_TITLE)))
						break
					}
				}
			}

			if OpenAPISwaggerCache == "" {
				stats["open_api_download"]++
				// get static/openapi.yml from the api
				res, err = http.Get(api + "/static/openapi.yml")
				if err != nil {
					log.Fatal(err)
				}

				// save res to static/openapi.yml in this directory
				openapi, err := ioutil.ReadAll(res.Body)
				if err != nil {
					log.Fatal(err)
				}

				OpenAPISwaggerCache = string(openapi)
			}

			// save
			err = ioutil.WriteFile("static/openapi.yml", []byte(OpenAPISwaggerCache), 0777)
			if err != nil {
				log.Fatal(err)
			}

			body = []byte(strings.ReplaceAll(string(body), "/static/openapi.yml", "static/openapi.yml"))

			fmt.Fprint(w, string(body))
			return
		}

		// fmt.Println(r.URL.Path)
		if _, ok := rpcEndpoints[r.URL.Path]; ok {
			HandleRequest(w, r, rpc, cfg, cache)
			return
		} else {
			HandleRequest(w, r, api, cfg, cache)
		}
	})

	// Start the server
	endpoint := cfg.APP_HOST + ":" + cfg.APP_PORT

	fmt.Println("Starting server on " + endpoint)
	http.ListenAndServe(endpoint, r)
	for {
		fmt.Println("Restarting on " + endpoint + " due to crash...")
		err := http.ListenAndServe(endpoint, r)
		if err != nil {
			fmt.Println(err.Error())
		}
	}
}
