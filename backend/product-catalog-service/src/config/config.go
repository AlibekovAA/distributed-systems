package config

import (
	"github.com/caarlos0/env/v11"
)

type Config struct {
	Database    DatabaseConfig `envPrefix:"DATABASE_"`
	Addr        string         `env:"ADDR"`
	RabbitMQURL string         `env:"RABBITMQ_URL"`
}

type DatabaseConfig struct {
	URI string `env:"URL"`
}

func LoadConfig() (*Config, error) {
	var cfg Config

	err := env.Parse(&cfg)

	if err != nil {
		return nil, err
	}

	return &cfg, nil
}
