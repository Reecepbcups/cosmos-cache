package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/mux"

	rpchttp "github.com/tendermint/tendermint/rpc/client/http"
)

// If I get a list of all RPC endpoints (GET and POST), can then smart route to REST endpoint through 1 URL.

const (
	rpc       = "https://rpc.juno.strange.love"
	api       = "https://api.juno.strange.love"
	websocket = "wss://rpc.juno.strange.love/websocket"
)

var (
	HTMLCache = ""

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
)

func blockSubscribe() {
	client, err := rpchttp.New(rpc)
	if err != nil {
		log.Fatal(err)
	}

	// Subscribe to new blocks
	eventCh, err := client.Subscribe(context.Background(), "test-client", "tm.event = 'NewBlock'")
	if err != nil {
		log.Fatal(err)
	}

	for event := range eventCh {
		fmt.Println(event)
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
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprint(w, HTMLCache)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	url := endpoint + r.URL.Path + "?" + r.URL.Query().Encode()

	if val, ok := cache[url]; ok {
		fmt.Println("Cache hit")
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

	// write the body to the response writer
	fmt.Fprint(w, string(body))
}

func main() {
	r := mux.NewRouter()

	// create a map which will be a 6 second cache
	cache := make(map[string]string)

	go blockSubscribe()

	go func() {
		for {
			cache = make(map[string]string)
			fmt.Println("Cache cleared")

			// This would be a websocket connection
			<-time.After(6 * time.Second)
		}
	}()

	// if route is static/openapi.yml, then show the swagger api
	r.HandleFunc("/static/openapi.yml", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("API hit")
		// read static/openapi.yml
		body, err := ioutil.ReadFile("static/openapi.yml")
		if err != nil {
			log.Fatal(err)
		}

		w.Header().Set("Content-Type", "text/html")
		fmt.Fprint(w, string(body))
	})

	// handle func for any route / wildcard
	r.HandleFunc("/{route:.*}", func(w http.ResponseWriter, r *http.Request) {

		// if path url is just /api, then show the swagger api
		if r.URL.Path == "/api" {
			fmt.Println("API hit")
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

			// save
			err = ioutil.WriteFile("static/openapi.yml", openapi, 0777)
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
	log.Fatal(http.ListenAndServe(":8080", r))
}
