package application

import (
	"encoding/json"
	database "main/src/db"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
)

// @Summary Получить баланс пользователя
// @Tags Users
// @Produce json
// @Param id path int true "ID пользователя"
// @Success 200
// @Router /users/{id}/balance [get]
func (app *Application) getBalance(w http.ResponseWriter, r *http.Request) {
	userID, err := strconv.Atoi(mux.Vars(r)["id"])
	if err != nil {
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	user, err := database.GetUser(app.DB, int64(userID))
	if err != nil {
		http.Error(w, "Failed get user from db", http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(user.Balance)
}
