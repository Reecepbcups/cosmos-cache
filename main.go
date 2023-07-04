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
	"github.com/joho/godotenv"

	rpchttp "github.com/cometbft/cometbft/rpc/client/http"
)

// If I get a list of all RPC endpoints (GET and POST), can then smart route to REST endpoint through 1 URL.

const (
	rpc                     = "https://rpc.juno.strange.love"
	api                     = "https://api.juno.strange.love"
	websocketUrl, websocket = "https://rpc.juno.strange.love:443", "/websocket"

	websocketPolling = 100 * time.Millisecond
)

var (
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
	}

	cache = make(map[string]string)

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
			cache = make(map[string]string)
			fmt.Println("Cache cleared")
		}
	}
}

func htmlView(w http.ResponseWriter, r *http.Request, body string) []byte {
	w.Header().Set("Content-Type", "text/html")

	baseRpc := strings.ReplaceAll(rpc, "http://", "")
	baseRpc = strings.ReplaceAll(baseRpc, "https://", "")

	return []byte(strings.ReplaceAll(body, baseRpc, r.Host))
}

func HandleRequest(w http.ResponseWriter, r *http.Request, endpoint string, cache map[string]string) {
	// if request is for /, then show the html view
	if r.URL.Path == "/" && HTMLCache != "" && endpoint == rpc {
		fmt.Println("HTML Cache hit")
		stats["HTML_CACHE"]++
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprint(w, HTMLCache)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	url := endpoint + r.URL.Path + "?" + r.URL.Query().Encode()

	if val, ok := cache[url]; ok {
		fmt.Println("Cache hit")
		stats["CACHE_"+endpoint]++
		fmt.Fprint(w, val)
		return
	}

	fmt.Println(url)
	res, err := http.Get(url)
	if err != nil {
		log.Fatal(err)
	}

	body, err := ioutil.ReadAll(res.Body)
	if err != nil {
		log.Fatal(err)
	}

	if string(body)[:6] == "<html>" {
		HTMLCache = string(htmlView(w, r, string(body)))
	}

	cache[url] = string(body)

	stats[endpoint]++
	fmt.Fprint(w, string(body))
}

func main() {
	if err := godotenv.Load(".env"); err != nil {
		log.Print("No .env file found")
	}

	r := mux.NewRouter()

	go blockSubscribe()

	httpClient := &http.Client{
		Timeout: time.Second * 10,
	}

	// panic | crash
	r.HandleFunc("/panic", func(w http.ResponseWriter, r *http.Request) {
		panic("Panic!")
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
		w.Header().Set("Content-Type", "application/json")

		prices := CoingeckoQuery(httpClient, "cosmos,canto,juno-network,osmosis,wynd", "eur,gbp,usd")
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
		// if path url is just /api, then show the swagger api
		if r.URL.Path == "/api" {
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

		fmt.Println(r.URL.Path)
		if _, ok := rpcEndpoints[r.URL.Path]; ok {
			HandleRequest(w, r, rpc, cache)
			return
		} else {
			HandleRequest(w, r, api, cache)
		}

	})

	// Start the server
	fmt.Print("Starting server on port http://localhost:8080...")
	http.ListenAndServe(":8080", r)
	for {
		fmt.Println("Restarting server on port http://localhost:8080 due to crash...")
		err := http.ListenAndServe(":8080", r)
		if err != nil {
			fmt.Println(err.Error())
		}
	}
}
