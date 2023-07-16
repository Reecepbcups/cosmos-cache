package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
)

func SwaggerAPICall(w http.ResponseWriter, r *http.Request, cfg *Config) {
	stats["rest_api"]++
	fmt.Println("REST API hit")
	// get api as http get
	w.Header().Set("Content-Type", "text/html")
	res, err := http.Get(cfg.REST_URL)
	if err != nil {
		log.Fatal(err)
	}

	body, err := io.ReadAll(res.Body)
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
		res, err = http.Get(cfg.REST_URL + "/static/openapi.yml")
		if err != nil {
			log.Fatal(err)
		}

		// save res to static/openapi.yml in this directory
		openapi, err := io.ReadAll(res.Body)
		if err != nil {
			log.Fatal(err)
		}

		OpenAPISwaggerCache = string(openapi)
	}

	// save
	err = os.WriteFile("static/openapi.yml", []byte(OpenAPISwaggerCache), 0777)
	if err != nil {
		log.Fatal(err)
	}

	body = []byte(strings.ReplaceAll(string(body), "/static/openapi.yml", "static/openapi.yml"))

	fmt.Fprint(w, string(body))
	return
}
