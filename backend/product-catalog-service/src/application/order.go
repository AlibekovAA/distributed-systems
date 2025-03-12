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

// @Summary Add an item to the cart
// @Tags Orders
// @Produce json
// @Success 200
// @Router /order/add [post]
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

// @Summary Get the user's current order
// @Tags Orders
// @Produce json
// @Param email path int true "User email"
// @Success 200
// @Router /order/{email} [get]
func (app *Application) getOrder(w http.ResponseWriter, r *http.Request) {
	email := mux.Vars(r)["email"]

	user, err := database.GetUserByEmail(app.DB, email)
	if err != nil {
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	orders, err := database.GetOrder(app.DB, user.Email)
	if err != nil {
		http.Error(w, "Failed get order for user", http.StatusInternalServerError)
		return
	}

	var products []models.Product

	for _, order := range orders {
		product, err := database.GetProduct(app.DB, order.ProductID)
		if err != nil {
			log.Printf("Failed get product from db %+v", err)
		}

		products = append(products, product)
	}

	json.NewEncoder(w).Encode(products)
}

// @Summary Delete an item from the shopping cart
// @Tags Orders
// @Produce json
// @Param email path int true "User email"
// @Param product_id path int true "ID of product"
// @Success 200
// @Router /order/{email}/{product_id} [delete]
func (app *Application) removeFromOrder(w http.ResponseWriter, r *http.Request) {
	email := mux.Vars(r)["email"]

	productID, err := strconv.Atoi(mux.Vars(r)["product_id"])
	if err != nil {
		http.Error(w, "Failed get product_id", http.StatusInternalServerError)
	}

	order := models.Order{
		ProductID: int64(productID),
		Email:     email,
	}

	log.Printf("order %+v", order)

	err = database.DeleteProductFromOrder(app.DB, order)
	if err != nil {
		log.Printf("Failed delete product %+v", err)

		http.Error(w, "Failed delete product from order", http.StatusInternalServerError)
		return
	}

	updatedOrder, err := database.GetOrder(app.DB, email)
	if err != nil {
		http.Error(w, "Failed to fetch updated cart", http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(updatedOrder)
}

// @Summary Pay for the order
// @Tags Orders
// @Produce json
// @Param email path int true "User email"
// @Success 200
// @Router /order/{email}/pay [post]
func (app *Application) payForOrder(w http.ResponseWriter, r *http.Request) {
	email := mux.Vars(r)["email"]

	user, err := database.GetUserByEmail(app.DB, email)
	if err != nil {
		http.Error(w, "Failed get id", http.StatusInternalServerError)
		return
	}

	var order models.Order

	if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
		http.Error(w, "Broken JSON", http.StatusBadRequest)
		return
	}

	order.Email = email

	exists, err := database.OrderExists(app.DB, order)
	if err != nil {
		http.Error(w, "Failed to check order", http.StatusInternalServerError)
		return
	}

	if !exists {
		http.Error(w, "Order not found", http.StatusNotFound)
		return
	}

	orders, err := database.GetOrder(app.DB, order.Email)
	if err != nil {
		http.Error(w, "Failed to calculate total price", http.StatusInternalServerError)
		return
	}

	totalPrice := 0

	var currentOrderNumber int64

	history, err := database.GetLastHistory(app.DB, user.ID)
	if err != nil {
		currentOrderNumber = 1
	} else {
		currentOrderNumber = history.OrderNumber + 1
	}

	historyRecords := []models.History{}

	for _, order := range orders {
		product, err := database.GetProduct(app.DB, order.ProductID)
		if err != nil {
			log.Printf("Failed to get product from order %+v", err)
			continue
		}

		historyRecord := models.History{
			OrderNumber: currentOrderNumber,
			UserID:      user.ID,
			ProductID:   order.ProductID,
		}

		historyRecords = append(historyRecords, historyRecord)

		totalPrice += int(product.Price)

		product.Quantity -= 1
	}

	if user.Balance < totalPrice {
		w.WriteHeader(http.StatusPaymentRequired)
		json.NewEncoder(w).Encode(map[string]string{
			"error":           "insufficient_funds",
			"message":         "Insufficient balance to complete the purchase",
			"required_amount": strconv.Itoa(totalPrice),
			"current_balance": strconv.Itoa(user.Balance),
		})
		return
	}

	user.Balance -= totalPrice

	err = database.UpdateUser(app.DB, user)
	if err != nil {
		http.Error(w, "Failed update user's balance", http.StatusInternalServerError)
		return
	}

	for _, record := range historyRecords {
		err = database.CreateHistoryRecord(app.DB, record)
		if err != nil {
			http.Error(w, "Failed create history record", http.StatusInternalServerError)
			return
		}
	}

	for _, order := range orders {
		product, err := database.GetProduct(app.DB, order.ProductID)
		if err != nil {
			log.Printf("Failed to get product from order %+v", err)
			continue
		}

		if product.Quantity < 3 {
			product.Quantity += 10

			err = database.UpdateProduct(app.DB, product)
			if err != nil {
				http.Error(w, "Failed to update product stock", http.StatusInternalServerError)
				return
			}
		}

	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Order paid successfully"})
}

// @Summary Clear shopping cart
// @Tags Orders
// @Produce json
// @Param email path int true "User email"
// @Success 200
// @Router /order/{email}/clear [post]
func (app *Application) clearCart(w http.ResponseWriter, r *http.Request) {
	email := mux.Vars(r)["email"]

	err := database.ClearUserCart(app.DB, email)
	if err != nil {
		http.Error(w, "Failed to clear cart", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Cart cleared successfully"})
}
