package application

import (
	"encoding/json"
	"log"
	database "main/src/db"
	"main/src/models"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
)

func (app *Application) addToOrder(w http.ResponseWriter, r *http.Request) {
	var order models.Order

	if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
		http.Error(w, "Broken JSON", http.StatusBadRequest)
		return
	}

	product, err := database.GetProduct(app.DB, order.ProductID)
	if err != nil {
		http.Error(w, "Failed get product from db", http.StatusInternalServerError)
		return
	}

	if product.Quantity <= 0 {
		http.Error(w, "Product is out of stock", http.StatusConflict)
		return
	}

	err = database.AddProductToOrder(app.DB, order)
	if err != nil {
		http.Error(w, "Failed to add product to order", http.StatusInternalServerError)
		return
	}

	product.Quantity -= 1

	err = database.UpdateProduct(app.DB, product)
	if err != nil {
		http.Error(w, "Failed to update product stock", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "Product added to cart"})
}

func (app *Application) getOrder(w http.ResponseWriter, r *http.Request) {
	userID, err := strconv.Atoi(mux.Vars(r)["user_id"])
	if err != nil {
		http.Error(w, "Failed get user_id", http.StatusInternalServerError)
	}

	orders, err := database.GetOrder(app.DB, int64(userID))
	if err != nil {
		http.Error(w, "Failed get order for user", http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(orders)
}

func (app *Application) removeFromOrder(w http.ResponseWriter, r *http.Request) {
	userID, err := strconv.Atoi(mux.Vars(r)["user_id"])
	if err != nil {
		http.Error(w, "Failed get user_id", http.StatusInternalServerError)
	}

	productID, err := strconv.Atoi(mux.Vars(r)["product_id"])
	if err != nil {
		http.Error(w, "Failed get product_id", http.StatusInternalServerError)
	}

	order := models.Order{
		ProductID: int64(productID),
		UserID:    int64(userID),
	}

	err = database.DeleteProductFromOrder(app.DB, order)
	if err != nil {
		http.Error(w, "Failed delete product from order", http.StatusInternalServerError)
		return
	}

	w.Write([]byte("Product was deleted from order"))
}

func (app *Application) payForOrder(w http.ResponseWriter, r *http.Request) {
	userID, err := strconv.Atoi(mux.Vars(r)["user_id"])
	if err != nil {
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	var order models.Order

	if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
		http.Error(w, "Broken JSON", http.StatusBadRequest)
		return
	}

	order.UserID = int64(userID)

	exists, err := database.OrderExists(app.DB, order)
	if err != nil {
		http.Error(w, "Failed to check order", http.StatusInternalServerError)
		return
	}

	if !exists {
		http.Error(w, "Order not found", http.StatusNotFound)
		return
	}

	orders, err := database.GetOrder(app.DB, order.UserID)
	if err != nil {
		http.Error(w, "Failed to calculate total price", http.StatusInternalServerError)
		return
	}

	totalPrice := 0

	for _, order := range orders {
		product, err := database.GetProduct(app.DB, order.ProductID)
		if err != nil {
			log.Printf("Failed to get product from order %+v", err)
			continue
		}

		totalPrice += int(product.Price)
	}

	user, err := database.GetUser(app.DB, order.UserID)
	if err != nil {
		http.Error(w, "Failed to get user from db", http.StatusInternalServerError)
		return
	}

	if user.Balance < totalPrice {
		http.Error(w, "Insufficient balance", http.StatusPaymentRequired)
		return
	}

	user.Balance -= totalPrice

	err = database.UpdateUser(app.DB, user)
	if err != nil {
		http.Error(w, "Failed update user's balance", http.StatusInternalServerError)
		return
	}

	var currentOrderNumber int64

	history, err := database.GetLastHistory(app.DB, user.ID)
	if err != nil {
		currentOrderNumber = 1
	} else {
		currentOrderNumber = history.OrderNumber + 1
	}

	historyRecord := models.History{
		OrderNumber: currentOrderNumber,
		UserID:      user.ID,
		ProductID:   order.ProductID,
	}

	err = database.CreateHistoryRecord(app.DB, historyRecord)
	if err != nil {
		http.Error(w, "Failed create history record", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Order paid successfully"})
}
