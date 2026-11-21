package application

import (
	"database/sql"
	"encoding/json"
	"errors"
	database "main/src/db"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
)

// @Summary User's order history
// @Tags Orders
// @Produce json
// @Security BearerAuth
// @Param email path string true "User email"
// @Success 200
// @Router /orders/{email}/history [get]
func (app *Application) getHistoryOrders(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/orders/{email}/history").Inc()

	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/orders/{email}/history"))
	defer timer.ObserveDuration()

	email, ok := requireOwnEmail(w, r, mux.Vars(r)["email"])
	if !ok {
		errorCount.WithLabelValues(r.Method, "/orders/{email}/history").Inc()
		return
	}

	user, err := database.GetUserByEmail(app.DB, email)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/orders/{email}/history").Inc()
		if errors.Is(err, sql.ErrNoRows) {
			writeJSONError(w, "User not found", http.StatusNotFound)
		} else {
			writeJSONError(w, "Failed get user", http.StatusInternalServerError)
		}
		return
	}

	history, err := database.GetHistoryResponses(app.DB, user.ID)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/orders/{email}/history").Inc()
		writeJSONError(w, "Failed to retrieve order history", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(history)
}
