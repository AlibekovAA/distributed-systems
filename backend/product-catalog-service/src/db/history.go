package database

import "main/src/models"

func GetHistoryResponses(db DB, userID int64) ([]models.HistoryResponse, error) {
	var rows []struct {
		OrderNumber int64  `db:"order_number"`
		ID          int64  `db:"id"`
		Name        string `db:"name"`
		Description string `db:"description"`
		Price       int64  `db:"price"`
		Quantity    int    `db:"quantity"`
	}
	err := db.Select(&rows, `
		SELECT h.order_number, p.id, p.name, p.description, p.price, p.quantity
		FROM history h
		JOIN product p ON p.id = h.product_id
		WHERE h.user_id = $1
		ORDER BY h.order_number, h.id`, userID)
	if err != nil {
		return nil, err
	}

	responses := make([]models.HistoryResponse, 0)
	for _, row := range rows {
		if len(responses) == 0 || responses[len(responses)-1].OrderNumber != row.OrderNumber {
			responses = append(responses, models.HistoryResponse{
				OrderNumber: row.OrderNumber,
				Items:       []models.Product{},
			})
		}

		response := &responses[len(responses)-1]
		response.Items = append(response.Items, models.Product{
			ID:          row.ID,
			Name:        row.Name,
			Description: row.Description,
			Price:       row.Price,
			Quantity:    row.Quantity,
		})
		response.TotalPrice += int(row.Price)
	}

	return responses, nil
}
