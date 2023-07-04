package main

import (
	"fmt"
	"log"

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
}

func LoadConfigFromFile(filename string) *Config {
	// load from the .env file as filename
	err := godotenv.Load(filename)
	if err != nil {
		log.Fatal(err)
	}

	var cfg Config
	err = envconfig.Process("", &cfg)
	if err != nil {
		panic(err)
	}

	// print cfg
	fmt.Printf("%+v\n", cfg)

	return &cfg
}
