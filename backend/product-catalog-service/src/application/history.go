package application

import (
	"encoding/json"
	database "main/src/db"
	"main/src/models"
	"net/http"

	"github.com/gorilla/mux"
)

// @Summary User's order history
// @Tags Orders
// @Produce json
// @Param email path int true "User email"
// @Success 200
// @Router /orders/{email}/history [get]
func (app *Application) getHistoryOrders(w http.ResponseWriter, r *http.Request) {
	email := mux.Vars(r)["email"]

	user, err := database.GetUserByEmail(app.DB, email)
	if err != nil {
		http.Error(w, "Failed get user", http.StatusInternalServerError)
		return
	}

	history, err := database.GetHistoryOrders(app.DB, user.ID)
	if err != nil {
		http.Error(w, "Failed to retrieve order history", http.StatusInternalServerError)
		return
	}

	historyMap := make(map[int64]*models.HistoryResponse)

	for _, record := range history {
		product, err := database.GetProduct(app.DB, record.ProductID)
		if err != nil {
			continue
		}

		if _, exists := historyMap[record.OrderNumber]; !exists {
			historyMap[record.OrderNumber] = &models.HistoryResponse{
				OrderNumber: record.OrderNumber,
				Items:      []models.Product{},
				TotalPrice: 0,
			}
		}

		historyMap[record.OrderNumber].Items = append(historyMap[record.OrderNumber].Items, product)
		historyMap[record.OrderNumber].TotalPrice += int(product.Price)
	}

	response := make([]models.HistoryResponse, 0, len(historyMap))
	for _, order := range historyMap {
		response = append(response, *order)
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}
