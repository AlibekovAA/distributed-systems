package models

import (
	"time"
)

type User struct {
	ID             int64     `db:"id"`
	Email          string    `db:"email"`
	HashedPassword string    `db:"hashed_password"`
	Name           string    `db:"name"`
	Balance        int       `db:"balance"`
	CreatedAt      time.Time `db:"created_at"`
	UpdatedAt      time.Time `db:"updated_at"`
}

type Product struct {
	ID          int64  `db:"id"`
	Name        string `db:"name"`
	Description string `db:"description"`
	Price       int64  `db:"price"`
	Quantity    int    `db:"quantity"`
}

type History struct {
	ID        int64 `db:"id"`
	UserID    int64 `db:"user_id"`
	ProductID int64 `db:"product_id"`
}

type Category struct {
	ID   int64  `db:"id"`
	Name string `db:"name"`
}

type ProductCategory struct {
	ProductID  int64 `db:"product_id"`
	CategoryID int64 `db:"category_id"`
}
