package config

import (
	"github.com/caarlos0/env/v11"
)

type Config struct {
	Database     DatabaseConfig `envPrefix:"DATABASE_"`
	Addr         string         `env:"ADDR" envDefault:":8080"`
	RabbitMQURL  string         `env:"RABBITMQ_URL,required"`
	JWTSecret    string         `env:"SECRET_KEY,required"`
	JWTAlgorithm string         `env:"ALGORITHM" envDefault:"HS256"`
}

type DatabaseConfig struct {
	URI string `env:"URL,required"`
}

func LoadConfig() (*Config, error) {
	var cfg Config

	err := env.Parse(&cfg)

	if err != nil {
		return nil, err
	}

	return &cfg, nil
}
