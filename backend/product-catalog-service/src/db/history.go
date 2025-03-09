package database

import "main/src/models"

func CreateHistoryRecord(db DB, history models.History) error {
	tx, err := db.Beginx()
	if err != nil {
		return err
	}

	query := `INSERT INTO "history" (user_id, product_id, order_number) VALUES ($1, $2, $3) RETURNING id`

	err = tx.QueryRowx(query, history.UserID, history.ProductID, history.OrderNumber).Scan(&history.ID)
	if err != nil {
		tx.Rollback()
		return err
	}

	return tx.Commit()
}

func GetLastHistory(db DB, userID int64) (models.History, error) {
	query := `SELECT * FROM "history" WHERE user_id = $1 ORDER BY order_id DESC LIMIT 1`

	var history models.History

	err := db.Get(&history, query, userID)
	if err != nil {
		return models.History{}, err
	}

	return history, nil
}

func GetHistoryOrders(db DB, userID int64) ([]models.History, error) {
	var history []models.History
	query := `SELECT * FROM "history" WHERE user_id = $1`

	err := db.Select(&history, query, userID)
	if err != nil {
		return nil, err
	}

	return history, nil
}
