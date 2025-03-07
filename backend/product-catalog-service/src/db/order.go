package database

import (
	"main/src/models"
)

func AddProductToOrder(db DB, order models.Order) error {
	tx, err := db.Beginx()
	if err != nil {
		return err
	}

	query := `INSERT INTO "order" (email, product_id) VALUES ($1, $2) RETURNING id`

	err = tx.QueryRowx(query, order.Email, order.ProductID).Scan(&order.ID)
	if err != nil {
		tx.Rollback()
		return err
	}

	return tx.Commit()
}

func GetOrder(db DB, email string) ([]models.Order, error) {
	query := `SELECT * FROM "order" WHERE email=$1`

	var orders []models.Order
	err := db.Select(&orders, query, email)
	if err != nil {
		return nil, err
	}

	return orders, err
}

func DeleteProductFromOrder(db DB, order models.Order) error {
	query := `DELETE FROM "order" WHERE email=$1 AND product_id=$2`
	_, err := db.Exec(query, order.Email, order.ProductID)

	return err
}

func OrderExists(db DB, order models.Order) (bool, error) {
	var exists bool
	query := `SELECT EXISTS(SELECT 1 FROM "order" WHERE email = $1)`
	err := db.Get(&exists, query, order.Email)

	return exists, err
}
