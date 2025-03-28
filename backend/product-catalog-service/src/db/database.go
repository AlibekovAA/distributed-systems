package database

import (
	"main/src/config"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

type DB = *sqlx.DB

func OpenDB(cfg *config.DatabaseConfig) (DB, error) {
	db, err := sqlx.Open("postgres", cfg.URI)
	if err != nil {
		return nil, err
	}

	return db, nil
}
