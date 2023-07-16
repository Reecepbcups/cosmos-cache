package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"
)

// Tx Response
type RPCResponse struct {
	Jsonrpc string `json:"jsonrpc"`
	ID      int    `json:"id"`
	Result  struct {
		Response struct {
			Code      int    `json:"code"`
			Log       string `json:"log"`
			Info      int    `json:"info"`
			Index     string `json:"index"`
			Key       any    `json:"key"`
			Value     string `json:"value"`
			ProofOps  any    `json:"proofOps"`
			Height    string `json:"height"`
			Codespace string `json:"codespace"`
		} `json:"response"`
	} `json:"result"`
}

type RPCRequest struct {
	Jsonrpc string `json:"jsonrpc"`
	ID      int    `json:"id"`
	Method  string `json:"method"`
	Params  struct {
		Data   string `json:"data"`
		Height string `json:"height"`
		Path   string `json:"path"`
		Prove  bool   `json:"prove"`
	} `json:"params"`
}

func (rq RPCRequest) String() string {
	return fmt.Sprintf("%s:%s,%s,%s,%v", rq.Method, rq.Params.Path, rq.Params.Data, rq.Params.Height, rq.Params.Prove)
}

var (
	HTMLCache           = ""
	OpenAPISwaggerCache = ""

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

func main() {
	cfg := LoadConfigFromFile(".env")
	cfg.LoadCacheTimes("cache_times.json")

	httpClient := http.Client{
		Timeout: time.Second * 10,
	}

	server := NewServer(httpClient, cfg, &cache)

	setFlags(cfg)

	go BlockSubscribe(cfg)

	server.Start(cfg.APP_HOST + ":" + cfg.APP_PORT)
}

func appendNewUrl(desc string, url string, breakBefore, breakAfter bool, r *http.Request, body string) []byte {
	text := ""
	if breakBefore {
		text = "<br>"
	}

	if desc != "" {
		text += desc
	}

	if len(url) > 0 {
		text += fmt.Sprintf("<br><a href=//%s%s>//%s%s</a>", r.Host, url, r.Host, url)
	}
	if breakAfter {
		text += "<br><br>"
	}

	return []byte(strings.ReplaceAll(body, "<div class='replace'>", text+"<div class='replace'>"))
}

func rpcHtmlView(w http.ResponseWriter, r *http.Request, cfg *Config, body string) []byte {
	w.Header().Set("Content-Type", "text/html")

	baseRpc := strings.ReplaceAll(cfg.RPC, "http://", "")
	baseRpc = strings.ReplaceAll(baseRpc, "https://", "")
	base := strings.ReplaceAll(body, baseRpc, r.Host)

	if cfg.RPC_CUSTOM_TEXT != "" {
		base = string(appendNewUrl(cfg.RPC_CUSTOM_TEXT, "", false, false, r, base))
	}

	if cfg.COINGECKO_ENABLED {
		base = string(appendNewUrl("Coingecko Asset Prices:", "/prices", true, true, r, base))
	}

	if cfg.RPC_TITLE != "" {
		title := fmt.Sprintf("<html><title>%s</title>", cfg.RPC_TITLE)
		base = strings.ReplaceAll(base, "<html>", title)
	}

	if cfg.REST_URL != "" {
		base = string(appendNewUrl("REST API:", "/api", false, true, r, base))
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
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	if r.Method == "GET" {
		// if request is for /, then show the html view
		if r.URL.Path == "/" && HTMLCache != "" && endpoint == cfg.RPC {
			// fmt.Println("HTML Cache hit")
			stats["HTML_CACHE"]++
			w.Header().Set("Content-Type", "text/html")

			fmt.Fprint(w, HTMLCache)
			return
		}

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

		body, err := io.ReadAll(res.Body)
		if err != nil {
			log.Fatal(err)
		}

		if strings.HasPrefix(string(body), "<html>") {
			body = []byte(strings.ReplaceAll(string(body), "<body><br>Available endpoints:<br><br>", "<div class='replace'>"))

			HTMLCache = string(rpcHtmlView(w, r, cfg, string(body)))
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
	} else if r.Method == "POST" {
		// TODO: mock id's replied back with
		if endpoint == cfg.REST_URL {
			fmt.Fprintf(w, `{"error":"This endpoint '%s' is not yet supported for the rest API (Req: %s)."}`, r.URL.Path, r.Method)
			return
		}

		var rpcReq RPCRequest
		reqBytes, _ := io.ReadAll(r.Body)

		if !strings.Contains(string(reqBytes), "<html>") {
			err := json.Unmarshal(reqBytes, &rpcReq)
			if err != nil {
				log.Fatal(err)
			}
		}

		// currentId := rpcReq.ID
		rpcReq.ID = -1

		// {"jsonrpc":"2.0","id":0,"method":"abci_query","params":{"data":"0A2B6A756E6F313072333966756570683966713761366C67737775347A64736738743367786C713637306C7430","height":"0","path":"/cosmos.auth.v1beta1.Query/Account","prove":false}}
		// marshal prePost and get it as a key

		// cacheKey := string(reqBytes)

		timeout := cfg.GetTimeout(r.URL.Path)
		if timeout == -1 {
			fmt.Fprintf(w, `{"error":"This endpoint '%s' is disabled."}`, r.URL.Path)
			return
		}

		// get id from the request
		// var prePost postRPC
		// var currentId int

		// jsonrpc, id, method, params

		// if err != nil {
		// 	panic(err)
		// }
		// fmt.Println(string(reqBytes))

		// if !strings.HasPrefix(string(respBytes), "<") {
		// 	err := json.NewDecoder(r.Body).Decode(&prePost)
		// 	if err != nil {
		// 		log.Fatal(err)
		// 	}
		// 	currentId = prePost.ID
		// 	fmt.Println(" - (id)", currentId)
		// }

		// print post
		// fmt.Println(" - (body)", r.Body)

		key := rpcReq.String()
		fmt.Println("-- (CacheKey)", key)
		if res := cache.Get(key); res != nil && rpcReq.Method != "broadcast_tx_sync" {
			// fmt.Println("res.Value", res.Value)
			// var resp RPCResponse
			var resp any
			err := json.Unmarshal([]byte(res.Value), &resp)
			if err != nil {
				// fmt.Println("err", err)
				return
			}
			// resp.ID = currentId

			// convert resp to json
			respBytes, err := json.Marshal(resp)
			if err != nil {
				log.Fatal(err)
			}

			// convert it to bytes, then Fprint it.

			fmt.Println("Cache hit", string(respBytes))

			// fmt.Println(string(respBytes))

			stats["CACHE_"+endpoint]++
			fmt.Fprint(w, respBytes)
			return
		}

		// try catch POST request, if first fails try RPC2

		var err error
		var res *http.Response
		RPCS := append([]string{cfg.RPC}, cfg.BACKUP_RPCS...)
		for _, rpc := range RPCS {
			res, err = http.Post(rpc, "application/json", strings.NewReader(string(reqBytes)))
			if err != nil {
				log.Printf("POST request to %s failed: %v", rpc, err)
				continue
			}
			break
		}

		// Request successful, handle the response and break the loop
		body, err := io.ReadAll(res.Body)
		if err != nil {
			log.Fatal(err)
		}
		// fmt.Println("body", string(body))

		// fmt.Println("res", res)
		// fmt.Println("bodybody", string(body)) // can be html

		// if body does not start with < , then load it into postRPC
		// var rpcResp RPCResponse
		var rpcResp any
		if !strings.Contains(string(body), "<html>") {
			err = json.Unmarshal(body, &rpcResp)
			if err != nil {
				log.Fatal(err)
			}
		}
		// rpcResp.ID = -1 -- since we unmarshal it later we can just replace anyways in the reply.

		// // print post
		fmt.Println(" - (body body)", string(body))

		// if strings.HasPrefix(string(body), "<html>") {
		// 	body = []byte(strings.ReplaceAll(string(body), "<body><br>Available endpoints:<br><br>", "<div class='replace'>"))

		// 	HTMLCache = string(rpcHtmlView(w, r, cfg, string(body)))
		// 	fmt.Fprint(w, HTMLCache)
		// 	return
		// }

		// load body into postRPC
		// var post postRPC
		// err = json.Unmarshal(body, &post)
		// if err != nil {
		// 	log.Fatal(err)
		// }

		// if path starts with /status, then we need to replace some of the data
		// TODO: fix this for post request.
		// if endpoint == cfg.RPC && strings.HasPrefix(r.URL.Path, "/status") {
		// 	body = hideStatusValues(cfg, body)
		// }

		// cacheRes, err := json.Marshal(post)
		// if err != nil {
		// 	log.Fatal(err)
		// }

		// convert rpcResp to string
		rpcRespBytes, err := json.Marshal(rpcResp)
		if err != nil {
			log.Fatal(err)
		}

		cache.Set(key, string(rpcRespBytes), timeout)

		stats[endpoint]++
		fmt.Fprint(w, string(body))
	}
}

func setFlags(cfg *Config) {
	host := flag.String("host", cfg.APP_HOST, "Host to listen on")
	port := flag.String("port", cfg.APP_PORT, "Port to listen on")
	flag.Parse()

	cfg.APP_HOST = *host
	cfg.APP_PORT = *port
}
