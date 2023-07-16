package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
)

func setTitle(cfg *Config, body []byte) []byte {
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
	return body
}

func swaggerUIFromCache(cfg *Config, body []byte) []byte {
	// Save new swagger UI if not already there, including in the file
	if OpenAPISwaggerCache == "" {
		stats["open_api_download"]++
		// get static/openapi.yml from the api
		res, err := http.Get(cfg.REST_URL + "/static/openapi.yml")
		if err != nil {
			log.Fatal(err)
		}

		// save res to static/openapi.yml in this directory
		// TODO: Limit cache time to like 30 minutes (because of upgrades)?
		openapi, err := io.ReadAll(res.Body)
		if err != nil {
			log.Fatal(err)
		}

		OpenAPISwaggerCache = string(openapi)

		err = os.WriteFile("static/openapi.yml", []byte(OpenAPISwaggerCache), 0777)
		if err != nil {
			log.Fatal(err)
		}
	}

	return []byte(strings.ReplaceAll(string(body), "/static/openapi.yml", "static/openapi.yml"))
}

func SwaggerAPICall(w http.ResponseWriter, r *http.Request, cfg *Config) {
	stats["rest_api"]++
	// fmt.Println("REST API hit")

	w.Header().Set("Content-Type", "text/html")
	res, err := http.Get(cfg.REST_URL)
	if err != nil {
		log.Fatal(err)
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		log.Fatal(err)
	}

	body = setTitle(cfg, body)

	body = swaggerUIFromCache(cfg, body)

	fmt.Fprint(w, string(body))
}
