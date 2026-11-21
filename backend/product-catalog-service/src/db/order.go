package database

import (
	"database/sql"
	"errors"
	"main/src/models"
	"sort"

	"github.com/jmoiron/sqlx"
	"github.com/lib/pq"
)

var (
	ErrInsufficientFunds = errors.New("insufficient funds")
	ErrOrderNotFound     = errors.New("order not found")
	ErrProductNotFound   = errors.New("product not found")
	ErrProductOutOfStock = errors.New("product is out of stock")
)

type CheckoutResult struct {
	RequiredAmount int
	CurrentBalance int
}

func AddProductToOrder(db DB, order models.Order) error {
	tx, err := db.Beginx()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = lockUserCart(tx, order.Email); err != nil {
		return err
	}

	var quantity int
	err = tx.Get(&quantity, `SELECT quantity FROM product WHERE id = $1 FOR UPDATE`, order.ProductID)
	if errors.Is(err, sql.ErrNoRows) {
		return ErrProductNotFound
	}
	if err != nil {
		return err
	}
	if quantity <= 0 {
		return ErrProductOutOfStock
	}

	if _, err = tx.Exec(
		`INSERT INTO "order" (email, product_id) VALUES ($1, $2)`,
		order.Email,
		order.ProductID,
	); err != nil {
		return err
	}

	if _, err = tx.Exec(`UPDATE product SET quantity = quantity - 1 WHERE id = $1`, order.ProductID); err != nil {
		return err
	}

	return tx.Commit()
}

func GetOrder(db DB, email string) ([]models.Order, error) {
	var orders []models.Order
	err := db.Select(&orders, `SELECT id, email, product_id FROM "order" WHERE email = $1 ORDER BY id`, email)
	return orders, err
}

func GetOrderProducts(db DB, email string) ([]models.Product, error) {
	var products []models.Product
	err := db.Select(&products, `
		SELECT p.id, p.name, p.description, p.price, p.quantity
		FROM "order" o
		JOIN product p ON p.id = o.product_id
		WHERE o.email = $1
		ORDER BY o.id`, email)
	return products, err
}

func DeleteProductFromOrder(db DB, order models.Order) error {
	tx, err := db.Beginx()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = lockUserCart(tx, order.Email); err != nil {
		return err
	}

	if _, err = tx.Exec(`
		WITH deleted AS (
			DELETE FROM "order"
			WHERE email = $1 AND product_id = $2
			RETURNING product_id
		)
		UPDATE product
		SET quantity = quantity + (SELECT COUNT(*) FROM deleted)
		WHERE id = $2 AND EXISTS (SELECT 1 FROM deleted)`,
		order.Email,
		order.ProductID,
	); err != nil {
		return err
	}

	return tx.Commit()
}

func ClearUserCart(db DB, email string) error {
	tx, err := db.Beginx()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = lockUserCart(tx, email); err != nil {
		return err
	}

	if _, err = tx.Exec(`
		UPDATE product AS p
		SET quantity = p.quantity + cart.quantity
		FROM (
			SELECT product_id, COUNT(*)::integer AS quantity
			FROM "order"
			WHERE email = $1
			GROUP BY product_id
		) AS cart
		WHERE p.id = cart.product_id`, email); err != nil {
		return err
	}

	if _, err = tx.Exec(`DELETE FROM "order" WHERE email = $1`, email); err != nil {
		return err
	}

	return tx.Commit()
}

func Checkout(db DB, email string) (CheckoutResult, error) {
	tx, err := db.Beginx()
	if err != nil {
		return CheckoutResult{}, err
	}
	defer tx.Rollback()
	if err = lockUserCart(tx, email); err != nil {
		return CheckoutResult{}, err
	}

	var user struct {
		ID      int64 `db:"id"`
		Balance int   `db:"balance"`
	}
	if err = tx.Get(&user, `SELECT id, balance FROM users WHERE email = $1 FOR UPDATE`, email); err != nil {
		return CheckoutResult{}, err
	}

	rows, err := tx.Queryx(`SELECT product_id FROM "order" WHERE email = $1 ORDER BY product_id, id FOR UPDATE`, email)
	if err != nil {
		return CheckoutResult{}, err
	}

	productCounts := make(map[int64]int)
	for rows.Next() {
		var productID int64
		if err = rows.Scan(&productID); err != nil {
			rows.Close()
			return CheckoutResult{}, err
		}
		productCounts[productID]++
	}
	if err = rows.Close(); err != nil {
		return CheckoutResult{}, err
	}
	if len(productCounts) == 0 {
		return CheckoutResult{}, ErrOrderNotFound
	}

	productIDs := sortedProductIDs(productCounts)
	var products []struct {
		ID       int64 `db:"id"`
		Price    int64 `db:"price"`
		Quantity int   `db:"quantity"`
	}
	if err = tx.Select(
		&products,
		`SELECT id, price, quantity FROM product WHERE id = ANY($1) ORDER BY id FOR UPDATE`,
		pq.Array(productIDs),
	); err != nil {
		return CheckoutResult{}, err
	}
	if len(products) != len(productIDs) {
		return CheckoutResult{}, ErrProductNotFound
	}

	totalPrice := 0
	for _, product := range products {
		totalPrice += int(product.Price) * productCounts[product.ID]
	}

	result := CheckoutResult{RequiredAmount: totalPrice, CurrentBalance: user.Balance}
	if user.Balance < totalPrice {
		return result, ErrInsufficientFunds
	}

	var orderNumber int64
	err = tx.Get(&orderNumber, `
		INSERT INTO user_order_counters (user_id, next_order_number)
		VALUES ($1, 2)
		ON CONFLICT (user_id) DO UPDATE
		SET next_order_number = user_order_counters.next_order_number + 1
		RETURNING next_order_number - 1`, user.ID)
	if err != nil {
		return CheckoutResult{}, err
	}

	if _, err = tx.Exec(`UPDATE users SET balance = balance - $1 WHERE id = $2`, totalPrice, user.ID); err != nil {
		return CheckoutResult{}, err
	}

	productCountValues := make([]int, len(productIDs))
	for index, productID := range productIDs {
		productCountValues[index] = productCounts[productID]
	}
	if _, err = tx.Exec(`
		INSERT INTO history (user_id, product_id, order_number)
		SELECT $1, products.product_id, $2
		FROM unnest($3::bigint[], $4::integer[]) WITH ORDINALITY AS products(product_id, quantity, position)
		CROSS JOIN LATERAL generate_series(1, products.quantity) AS copies(copy_number)
		ORDER BY products.position, copies.copy_number`,
		user.ID,
		orderNumber,
		pq.Array(productIDs),
		pq.Array(productCountValues),
	); err != nil {
		return CheckoutResult{}, err
	}

	if _, err = tx.Exec(
		`UPDATE product SET quantity = quantity + 10 WHERE id = ANY($1) AND quantity < 3`,
		pq.Array(productIDs),
	); err != nil {
		return CheckoutResult{}, err
	}

	if _, err = tx.Exec(`DELETE FROM "order" WHERE email = $1`, email); err != nil {
		return CheckoutResult{}, err
	}

	return result, tx.Commit()
}

func sortedProductIDs(counts map[int64]int) []int64 {
	ids := make([]int64, 0, len(counts))
	for id := range counts {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { return ids[i] < ids[j] })
	return ids
}

func lockUserCart(tx *sqlx.Tx, email string) error {
	_, err := tx.Exec(`SELECT pg_advisory_xact_lock(hashtext($1))`, email)
	return err
}
