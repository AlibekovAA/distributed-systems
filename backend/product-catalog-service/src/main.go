package main

import (
	"context"
	"log"
	"main/src/application"
	"main/src/config"
	"os"
	"os/signal"

	_ "github.com/lib/pq"
)

func main() {
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("failed load config %+v", err)
	}

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)

	defer cancel()

	app := application.NewApplication()

	err = app.Configure(ctx, cfg)
	if err != nil {
		log.Fatalf("failed configure application %+v", err)
	}

	app.Run(ctx)
}
