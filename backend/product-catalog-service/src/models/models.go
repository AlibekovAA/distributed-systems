package models

import (
	"time"
)

type User struct {
	ID             int64     `db:"id" json:"id"`
	Email          string    `db:"email" json:"email"`
	HashedPassword string    `db:"hashed_password" json:"-"`
	Name           string    `db:"name" json:"name"`
	Balance        int       `db:"balance" json:"balance"`
	CreatedAt      time.Time `db:"created_at" json:"created_at"`
}

type Product struct {
	ID          int64  `db:"id" json:"id"`
	Name        string `db:"name" json:"name"`
	Description string `db:"description" json:"description"`
	Price       int64  `db:"price" json:"price"`
	Quantity    int    `db:"quantity" json:"quantity"`
}

type History struct {
	ID          int64 `db:"id" json:"id"`
	UserID      int64 `db:"user_id" json:"user_id"`
	ProductID   int64 `db:"product_id" json:"product_id"`
	OrderNumber int64 `db:"order_number" json:"order_number"`
}

type Category struct {
	ID   int64  `db:"id" json:"id"`
	Name string `db:"name" json:"name"`
}

type ProductCategory struct {
	ProductID  int64 `db:"product_id" json:"product_id"`
	CategoryID int64 `db:"category_id" json:"category_id"`
}

type Order struct {
	ID        int64  `db:"id" json:"id"`
	Email     string `db:"email" json:"email"`
	ProductID int64  `db:"product_id" json:"product_id"`
}

type HistoryResponse struct {
	OrderNumber int64     `json:"order_number"`
	Items      []Product `json:"items"`
	TotalPrice int       `json:"total_price"`
}

type RecommendationResponse struct {
	UserID          int64    `json:"user_id"`
	Recommendations []Product `json:"recommendations"`
}
