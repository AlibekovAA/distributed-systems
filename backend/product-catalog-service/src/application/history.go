package application

import (
	"encoding/json"
	database "main/src/db"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
)

func (app *Application) getHistoryOrders(w http.ResponseWriter, r *http.Request) {
	userID, err := strconv.Atoi(mux.Vars(r)["user_id"])
	if err != nil {
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	history, err := database.GetHistoryOrders(app.DB, int64(userID))
	if err != nil {
		http.Error(w, "Failed to retrieve order history", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(history)
}
