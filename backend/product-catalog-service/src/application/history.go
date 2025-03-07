package application

import (
	"encoding/json"
	database "main/src/db"
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
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	history, err := database.GetHistoryOrders(app.DB, user.ID)
	if err != nil {
		http.Error(w, "Failed to retrieve order history", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(history)
}
