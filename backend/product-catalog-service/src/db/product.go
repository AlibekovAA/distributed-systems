package database

import (
	"main/src/models"
)

func CreateProduct(db DB, product models.Product) error {
	tx, err := db.Beginx()
	if err != nil {
		return err
	}

	query := `INSERT INTO product (name, description, price, quantity) VALUES ($1, $2, $3, $4) RETURNING id`

	err = tx.QueryRowx(query, product.Name, product.Description, product.Price, product.Quantity).Scan(&product.ID)
	if err != nil {
		tx.Rollback()
		return err
	}

	return tx.Commit()
}

func GetProducts(db DB) ([]models.Product, error) {
	query := `SELECT * FROM product`

	var products []models.Product
	err := db.Select(&products, query)
	if err != nil {
		return nil, err
	}

	return products, err
}

func DeleteProduct(db DB, id int) error {
	query := `DELETE FROM product WHERE id=$1`
	_, err := db.Exec(query, id)

	return err
}

func GetProduct(db DB, id int64) (models.Product, error) {
	query := `SELECT * FROM product WHERE id=$1`

	var product models.Product
	err := db.Get(&product, query, id)
	if err != nil {
		return models.Product{}, err
	}

	return product, err
}

func UpdateProduct(db DB, product models.Product) error {
	query := `UPDATE product SET name = :name, description = :description, price = :price, quantity = :quantity WHERE id = :id`

	_, err := db.NamedExec(query, product)

	return err
}
