package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/gorilla/mux"
)

type Server struct {
	router mux.Router
	client http.Client

	cfg *Config

	cache *Cache
}

func NewServer(client http.Client, config *Config, cache *Cache) *Server {
	return &Server{
		router: *mux.NewRouter(),
		client: client,
		cfg:    config,
		cache:  cache,
	}
}

func (s *Server) SetPanicHandler() *mux.Route {
	return s.router.HandleFunc("/panic", func(w http.ResponseWriter, r *http.Request) {
		panic("Panic!")
	})
}

func (s *Server) SetStatisticsHandler() *mux.Route {
	return s.router.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		statsJson, err := json.Marshal(stats)
		if err != nil {
			log.Fatal(err)
		}

		fmt.Fprint(w, string(statsJson))
	})
}

func (s *Server) SetOpenAPICacheHandler() *mux.Route {
	return s.router.HandleFunc("/static/openapi.yml", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("OpenAPI cache hit")

		w.Header().Set("Content-Type", "text/html")

		if len(OpenAPISwaggerCache) > 0 {
			stats["open_api_cache"]++
			fmt.Fprint(w, OpenAPISwaggerCache)
			return
		}

		body, err := os.ReadFile("static/openapi.yml")
		if err != nil {
			log.Fatal(err)
		}

		stats["open_api"]++

		OpenAPISwaggerCache = string(body)
		fmt.Fprint(w, OpenAPISwaggerCache)
	})
}

func (s *Server) SetCoingeckoHandler() *mux.Route {
	return s.router.HandleFunc("/prices", func(w http.ResponseWriter, r *http.Request) {
		if !s.cfg.COINGECKO_ENABLED {
			fmt.Fprint(w, "Coingecko not enabled on this node.")
			return
		}
		w.Header().Set("Content-Type", "application/json")

		prices := CoingeckoQuery(s.client, s.cfg.COINGECKO_IDS, s.cfg.COINGECKO_FIAT)
		pricesJson, err := json.Marshal(prices)
		if err != nil {
			log.Fatal(err)
		}

		stats["prices"]++

		fmt.Fprint(w, string(pricesJson))
	})
}

func (s *Server) SetFaviconCacheHandler() *mux.Route {
	return s.router.HandleFunc("/favicon.ico", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "image/x-icon")

		if res := cache.Get("favicon.ico"); res != nil {
			fmt.Println("Favicon cache hit")
			stats["CACHE_favicon"]++
			fmt.Fprint(w, res.Value)
			return
		}

		body, err := os.ReadFile("static/favicon.png")
		if err != nil {
			log.Fatal(err)
		}
		cache.Set("favicon.ico", string(body), int(30*time.Minute.Seconds()))
		fmt.Fprint(w, string(body))
	})
}

func (s *Server) SetWildCardEndpointHandler() *mux.Route {
	return s.router.HandleFunc("/{route:.*}", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api" || r.URL.Path == "/swagger" {
			SwaggerAPICall(w, r, s.cfg)
		}

		if _, ok := rpcEndpointsTM34[r.URL.Path]; ok {
			HandleRequest(w, r, s.cfg.RPC, s.cfg, cache)
			return
		} else {
			HandleRequest(w, r, s.cfg.REST_URL, s.cfg, cache)
		}
	})
}

func (s *Server) Start(endpoint string) {
	// Handlers.
	s.SetPanicHandler()
	s.SetStatisticsHandler()
	s.SetFaviconCacheHandler()
	s.SetCoingeckoHandler()
	s.SetOpenAPICacheHandler()
	s.SetWildCardEndpointHandler()

	// Listening and catching panics.
	fmt.Println("Starting server on http://" + endpoint)
	http.ListenAndServe(endpoint, &s.router)
	for {
		fmt.Println("Restarting on http://" + endpoint + " due to crash...")
		err := http.ListenAndServe(endpoint, &s.router)
		if err != nil {
			fmt.Println(err.Error())
			if strings.Contains(err.Error(), "address already in use") {
				time.Sleep(5 * time.Second)
				continue
			}
		}
	}
}
