package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"regexp"
	"strings"

	"github.com/iancoleman/orderedmap"
	"github.com/joho/godotenv"
	"github.com/kelseyhightower/envconfig"
)

type Config struct {
	DEBUGGING    bool `envconfig:"DEBUGGING"`
	ENABLE_STATS bool `envconfig:"ENABLE_STATS"`

	USE_BACKUP  bool     `envconfig:"USE_BACKUP"`
	RPC         string   `envconfig:"RPC_URL"`
	BACKUP_RPCS []string `envconfig:"BACKUP_RPC_URLS"`

	// ws://1.1.1.1:26657/websocket
	RPC_WEBSOCKET        string `envconfig:"RPC_WEBSOCKET"`
	BACKUP_RPC_WEBSOCKET string `envconfig:"BACKUP_RPC_WEBSOCKETS"`

	REST_URL           string `envconfig:"REST_URL"`
	BACKUP_REST_URLS   string `envconfig:"BACKUP_REST_URLS"`
	DISABLE_SWAGGER_UI bool   `envconfig:"DISABLE_SWAGGER_UI"`

	// === Security ===
	RPC_LISTEN_ADDRESS string `envconfig:"RPC_LISTEN_ADDRESS"`
	NODE_MONIKER       string `envconfig:"NODE_MONIKER"`
	NODE_TM_VERSION    string `envconfig:"NODE_TM_VERSION"`

	// cOINGECKO
	COINGECKO_ENABLED bool   `envconfig:"COINGECKO_ENABLED"`
	COINGECKO_IDS     string `envconfig:"COINGECKO_IDS"`
	COINGECKO_FIAT    string `envconfig:"COINGECKO_FIAT"`

	// Cosmetic HTML
	RPC_TITLE       string `envconfig:"RPC_TITLE"`
	API_TITLE       string `envconfig:"API_TITLE"`
	RPC_CUSTOM_TEXT string `envconfig:"RPC_CUSTOM_TEXT"`
	// TODO: Dark mode?

	APP_HOST string `envconfig:"APP_HOST"`
	APP_PORT string `envconfig:"APP_PORT"`

	CACHE_TIMES *orderedmap.OrderedMap `json:"-"`
}

func (c *Config) GetTimeout(path string) int {
	if c.CACHE_TIMES == nil {
		return DefaultCacheTimeSeconds
	}

	if strings.HasPrefix(path, "/favicon.ico") {
		return 0
	}

	for _, expr := range c.CACHE_TIMES.Keys() {
		if match, _ := regexp.MatchString(expr, path); match {
			seconds, _ := c.CACHE_TIMES.Get(expr)

			if c.DEBUGGING {
				fmt.Printf("Regex match: %s %v (expr:%s)\n", path, seconds, expr)
			}

			return int(seconds.(float64))
		}
	}

	return DefaultCacheTimeSeconds
}

func LoadConfigFromFile(filename string) *Config {
	err := godotenv.Load(filename)
	if err != nil {
		log.Fatal(err)
	}

	var cfg Config
	err = envconfig.Process("", &cfg)
	if err != nil {
		panic(err)
	}

	return &cfg
}

func (config *Config) LoadCacheTimes(filename string) {
	jsonData, err := os.ReadFile(filename)
	if err != nil {
		log.Fatal(err)
	}

	om := orderedmap.New()

	err = json.Unmarshal(jsonData, &om)
	if err != nil {
		log.Fatal(err)
	}

	config.CACHE_TIMES = om
}
