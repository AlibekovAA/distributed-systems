package application

import (
	"encoding/json"
	database "main/src/db"
	"net/http"
)

func (app *Application) topUpBalance(w http.ResponseWriter, r *http.Request) {
	var data struct {
		UserID int `json:"user_id"`
		Amount int `json:"amount"`
	}

	if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
		http.Error(w, "Неверный JSON", http.StatusBadRequest)
		return
	}

	user, err := database.GetUser(app.DB, data.UserID)
	if err != nil {
		http.Error(w, "Failed get user from db", http.StatusInternalServerError)
		return
	}

	user.Balance += data.Amount

	err = database.UpdateUser(app.DB, user)
	if err != nil {
		http.Error(w, "Failed update user's balance", http.StatusInternalServerError)
		return
	}

	w.Write([]byte("Баланс пополнен"))
}
