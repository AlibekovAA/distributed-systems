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

// @Summary Create a new product
// @Tags Products
// @Produce json
// @Success 201
// @Router /products [post]
func (app *Application) createProduct(w http.ResponseWriter, r *http.Request) {
	var product models.Product
	if err := json.NewDecoder(r.Body).Decode(&product); err != nil {
		http.Error(w, "Broken JSON", http.StatusBadRequest)
		return
	}

	err := database.CreateProduct(app.DB, product)
	if err != nil {
		http.Error(w, "Failed create product", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(product)
}

// @Summary Get a list of products
// @Tags Products
// @Produce json
// @Param email path string true "User Email"
// @Success 200 {array} string
// @Router /products/{email} [get]
func (app *Application) getProducts(w http.ResponseWriter, r *http.Request) {
	email := mux.Vars(r)["email"]
	log.Printf("Received request for email: %s", email)

	if email == "" {
		http.Error(w, "Email is required", http.StatusBadRequest)
		return
	}

	user, err := database.GetUserByEmail(app.DB, email)
	if err != nil {
		log.Printf("Error getting user by email: %v", err)
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}
	log.Printf("Found user with ID: %d", user.ID)

	_, err = app.RabbitChannel.QueueDeclare(
		responseQueue, false, false, false, false, nil,
	)

	if err != nil {
		log.Printf("Failed to declare a response queue %+v", err)
	}

	userIDStr := strconv.Itoa(int(user.ID))
	log.Printf("Sending request to recommendation service with user ID: %s", userIDStr)
	err = sendRequest(app.RabbitChannel, userIDStr)

	if err != nil {
		log.Printf("Failed to send request %+v", err)
	}

	response := receiveResponse(app.RabbitChannel)
	log.Printf("Received response from recommendation service: %s", response)

	var recommendationResponse struct {
		UserID int64 `json:"user_id"`
		Recommendations []models.Product `json:"recommendations"`
	}

	if err := json.Unmarshal([]byte(response), &recommendationResponse); err != nil {
		log.Printf("Failed to parse recommendation response: %v", err)
		products, err := database.GetProducts(app.DB)
		if err != nil {
			http.Error(w, "Failed get products", http.StatusInternalServerError)
			return
		}
		json.NewEncoder(w).Encode(products)
		return
	}

	json.NewEncoder(w).Encode(recommendationResponse.Recommendations)
}

// @Summary Delete a product
// @Tags Products
// @Produce json
// @Success 200 {array} string
// @Router /products [delete]
func (app *Application) deleteProduct(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.Atoi(mux.Vars(r)["id"])
	if err != nil {
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	err = database.DeleteProduct(app.DB, id)
	if err != nil {
		http.Error(w, "Failed delete the product", http.StatusInternalServerError)
		return
	}

	w.Write([]byte("Product was deleted"))
}
