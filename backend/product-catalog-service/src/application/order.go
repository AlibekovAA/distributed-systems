package application

import (
	"database/sql"
	"encoding/json"
	"errors"
	database "main/src/db"
	"main/src/models"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
)

// @Summary Add an item to the cart
// @Tags Orders
// @Produce json
// @Security BearerAuth
// @Success 201
// @Router /order/add [post]
func (app *Application) addToOrder(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/order/add").Inc()
	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/order/add"))
	defer timer.ObserveDuration()

	var order models.Order
	if !decodeJSONBody(w, r, &order) {
		errorCount.WithLabelValues(r.Method, "/order/add").Inc()
		return
	}
	if order.ProductID <= 0 {
		errorCount.WithLabelValues(r.Method, "/order/add").Inc()
		writeJSONError(w, "product_id must be positive", http.StatusBadRequest)
		return
	}
	order.Email = authenticatedEmail(r)

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/order/add").Inc()
		switch {
		case errors.Is(err, database.ErrProductNotFound):
			writeJSONError(w, "Product not found", http.StatusNotFound)
		case errors.Is(err, database.ErrProductOutOfStock):
			writeJSONError(w, "Product is out of stock", http.StatusConflict)
		default:
			writeJSONError(w, "Failed to add product to order", http.StatusInternalServerError)
		}
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "Product added to cart"})
}

// @Summary Get the user's current order
// @Tags Orders
// @Produce json
// @Security BearerAuth
// @Param email path string true "User email"
// @Success 200
// @Router /order/{email} [get]
func (app *Application) getOrder(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/order/{email}").Inc()
	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/order/{email}"))
	defer timer.ObserveDuration()

	email, ok := requireOwnEmail(w, r, mux.Vars(r)["email"])
	if !ok {
		errorCount.WithLabelValues(r.Method, "/order/{email}").Inc()
		return
	}

	if _, err := database.GetUserByEmail(app.DB, email); err != nil {
		errorCount.WithLabelValues(r.Method, "/order/{email}").Inc()
		if errors.Is(err, sql.ErrNoRows) {
			writeJSONError(w, "User not found", http.StatusNotFound)
		} else {
			writeJSONError(w, "Failed get user", http.StatusInternalServerError)
		}
		return
	}

	products, err := database.GetOrderProducts(app.DB, email)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/order/{email}").Inc()
		writeJSONError(w, "Failed get order for user", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(products)
}

// @Summary Delete an item from the shopping cart
// @Tags Orders
// @Produce json
// @Security BearerAuth
// @Param email path string true "User email"
// @Param product_id path int true "ID of product"
// @Success 200
// @Router /order/{email}/{product_id} [delete]
func (app *Application) removeFromOrder(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/order/{email}/{product_id}").Inc()
	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/order/{email}/{product_id}"))
	defer timer.ObserveDuration()

	email, ok := requireOwnEmail(w, r, mux.Vars(r)["email"])
	if !ok {
		errorCount.WithLabelValues(r.Method, "/order/{email}/{product_id}").Inc()
		return
	}

	productID, err := strconv.Atoi(mux.Vars(r)["product_id"])
	if err != nil || productID <= 0 {
		errorCount.WithLabelValues(r.Method, "/order/{email}/{product_id}").Inc()
		writeJSONError(w, "Invalid product_id", http.StatusBadRequest)
		return
	}

	order := models.Order{ProductID: int64(productID), Email: email}
	if err = database.DeleteProductFromOrder(app.DB, order); err != nil {
		errorCount.WithLabelValues(r.Method, "/order/{email}/{product_id}").Inc()
		writeJSONError(w, "Failed delete product from order", http.StatusInternalServerError)
		return
	}

	updatedOrder, err := database.GetOrder(app.DB, email)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/order/{email}/{product_id}").Inc()
		writeJSONError(w, "Failed to fetch updated cart", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(updatedOrder)
}

// @Summary Pay for the order
// @Tags Orders
// @Produce json
// @Security BearerAuth
// @Param email path string true "User email"
// @Success 200
// @Router /order/{email}/pay [post]
func (app *Application) payForOrder(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/order/{email}/pay").Inc()
	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/order/{email}/pay"))
	defer timer.ObserveDuration()

	email, ok := requireOwnEmail(w, r, mux.Vars(r)["email"])
	if !ok {
		errorCount.WithLabelValues(r.Method, "/order/{email}/pay").Inc()
		return
	}

	var order models.Order
	if !decodeJSONBody(w, r, &order) {
		errorCount.WithLabelValues(r.Method, "/order/{email}/pay").Inc()
		return
	}

	result, err := database.Checkout(app.DB, email)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/order/{email}/pay").Inc()
		switch {
		case errors.Is(err, database.ErrInsufficientFunds):
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusPaymentRequired)
			json.NewEncoder(w).Encode(map[string]string{
				"error":           "insufficient_funds",
				"message":         "Insufficient balance to complete the purchase",
				"required_amount": strconv.Itoa(result.RequiredAmount),
				"current_balance": strconv.Itoa(result.CurrentBalance),
			})
		case errors.Is(err, database.ErrOrderNotFound):
			writeJSONError(w, "Order not found", http.StatusNotFound)
		case errors.Is(err, sql.ErrNoRows):
			writeJSONError(w, "User not found", http.StatusNotFound)
		default:
			writeJSONError(w, "Failed to pay for order", http.StatusInternalServerError)
		}
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Order paid successfully"})
}

// @Summary Clear shopping cart
// @Tags Orders
// @Produce json
// @Security BearerAuth
// @Param email path string true "User email"
// @Success 200
// @Router /order/{email}/clear [post]
func (app *Application) clearCart(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/order/{email}/clear").Inc()
	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/order/{email}/clear"))
	defer timer.ObserveDuration()

	email, ok := requireOwnEmail(w, r, mux.Vars(r)["email"])
	if !ok {
		errorCount.WithLabelValues(r.Method, "/order/{email}/clear").Inc()
		return
	}

	if err := database.ClearUserCart(app.DB, email); err != nil {
		errorCount.WithLabelValues(r.Method, "/order/{email}/clear").Inc()
		writeJSONError(w, "Failed to clear cart", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Cart cleared successfully"})
}
