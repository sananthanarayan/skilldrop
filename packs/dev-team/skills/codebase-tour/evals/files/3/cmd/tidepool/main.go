package main

import (
	"context"
	"log"
	"net/http"

	"example.com/tidepool/internal/config"
	"example.com/tidepool/internal/dispatch"
	"example.com/tidepool/internal/store"
)

func main() {
	cfg, err := config.FromEnv()
	if err != nil {
		log.Fatalf("config: %v", err)
	}
	db, err := store.Open(context.Background(), cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("store: %v", err)
	}
	d := dispatch.New(cfg, store.New(db), dispatch.NewHTTPSender(http.DefaultClient))
	log.Fatal(d.Run(context.Background()))
}
