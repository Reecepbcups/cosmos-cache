package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"
)

// {
// 	"coins": {
// 	"ATOM": {
// 	"coingecko-id": "cosmos",
// 	"prices": {
// 	"eur": 9.01,
// 	"gbp": 7.74,
// 	"usd": 9.83
// 	}
// 	},
// 	"CANTO": {
// 	"coingecko-id": "canto",
// 	"prices": {
// 	"eur": 0.108036,
// 	"gbp": 0.092821,
// 	"usd": 0.117814
// 	}
// 	},
// 	"JUNO": {
// 	"coingecko-id": "juno-network",
// 	"prices": {
// 	"eur": 0.259842,
// 	"gbp": 0.223247,
// 	"usd": 0.283359
// 	}
// 	},
// 	"OSMO": {
// 	"coingecko-id": "osmosis",
// 	"prices": {
// 	"eur": 0.468388,
// 	"gbp": 0.402422,
// 	"usd": 0.510779
// 	}
// 	},
// 	"WYND": {
// 	"coingecko-id": "wynd",
// 	"prices": {
// 	"eur": 0.01560466,
// 	"gbp": 0.01340697,
// 	"usd": 0.01701697
// 	}
// 	}
// 	},
// 	"last_update": 1688444985
// 	}

const CG_URL = "https://api.coingecko.com/api/v3"

var (
	symbols = map[string]Symbol{}
	CGCache = Prices{}
)

type Prices struct {
	Coins      map[string]Coin `json:"coins"`
	LastUpdate int64           `json:"last_update"`
}

type Coin struct {
	CoingeckoId string             `json:"coingecko_id"`
	Prices      map[string]float64 `json:"prices"`
}

func CoingeckoQuery(client http.Client, ids string, vs_currencies string) Prices {
	now := time.Now().Unix()

	if len(symbols) == 0 {
		for _, symbol := range GetSymbols(client, ids) {
			symbols[strings.ToUpper(symbol.Symbol)] = symbol
		}
	}

	if len(CGCache.Coins) > 0 {
		if now-CGCache.LastUpdate < 15 {
			fmt.Printf("Using CG cache\n")
			return CGCache
		}
	}

	url := fmt.Sprintf(`%s/simple/price?ids=%s&vs_currencies=%s`, CG_URL, ids, vs_currencies)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		log.Fatal(err)
	}

	resp, err := client.Do(req)
	if err != nil {
		log.Fatal(err)
	}

	defer resp.Body.Close()
	bodyText, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}

	type fiatprices map[string]map[string]float64

	var fiat fiatprices
	// fmt.Printf("%s\n", bodyText)
	// {"bitcoin":{"usd":31123},"cosmos":{"usd":9.83}}

	err = json.Unmarshal(bodyText, &fiat)
	if err != nil {
		log.Fatal(err)
	}

	p := Prices{}
	p.Coins = make(map[string]Coin, len(symbols))
	p.LastUpdate = now

	for k, v := range symbols {
		p.Coins[k] = Coin{
			CoingeckoId: v.Id,
			Prices:      map[string]float64{},
		}

		// iterate fiat for each symbol
		for fiat_symbol, fiat_prices := range fiat {
			if fiat_symbol == v.Id {
				for fiat_currency, fiat_price := range fiat_prices {
					p.Coins[k].Prices[fiat_currency] = fiat_price
				}
			}
		}
	}

	CGCache = p
	return p
}

type Symbol struct {
	Id     string `json:"id"`
	Symbol string `json:"symbol"`
	Name   string `json:"name"`
}

func GetSymbols(client http.Client, ids string) []Symbol {
	groups := []Symbol{}

	for _, id := range strings.Split(ids, ",") {

		// https://api.coingecko.com/api/v3/coins/cosmos
		url := fmt.Sprintf(`%s/coins/%s`, CG_URL, id)
		req, err := http.NewRequest("GET", url, nil)
		if err != nil {
			log.Fatal(err)
		}

		resp, err := client.Do(req)
		if err != nil {
			log.Fatal(err)
		}

		defer resp.Body.Close()

		bodyText, err := io.ReadAll(resp.Body)
		if err != nil {
			log.Fatal(err)
		}

		// decode json into Symbol
		var s Symbol
		err = json.Unmarshal(bodyText, &s)
		if err != nil {
			log.Fatal(err)
		}

		groups = append(groups, s)

		// fmt.Printf("%v\n", s)
	}

	return groups
}
