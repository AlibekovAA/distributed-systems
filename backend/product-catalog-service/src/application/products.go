package application

import (
	"encoding/json"
	database "main/src/db"
	"main/src/models"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
)

// @Summary Create a new product
// @Tags Products
// @Produce json
// @Success 201
// @Router /products [post]
func (app *Application) createProduct(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/products").Inc()
	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/products"))
	defer timer.ObserveDuration()

	var product models.Product
	if err := json.NewDecoder(r.Body).Decode(&product); err != nil {
		errorCount.WithLabelValues(r.Method, "/products").Inc()
		http.Error(w, "Broken JSON", http.StatusBadRequest)
		return
	}

	err := database.CreateProduct(app.DB, product)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products").Inc()
		http.Error(w, "Failed create product", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(product)
}

// @Summary Get a list of products
// @Tags Products
// @Produce json
// @Param email path string true "User email"
// @Success 200 {array} string
// @Router /products/{email} [get]
func (app *Application) getProducts(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/products/{email}").Inc()

	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/products/{email}"))
	defer timer.ObserveDuration()

	email := mux.Vars(r)["email"]
	if email == "" {
		errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
		http.Error(w, "Email is required", http.StatusBadRequest)
		return
	}

	user, err := database.GetUserByEmail(app.DB, email)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	userIDStr := strconv.Itoa(int(user.ID))

	correlationID, queueName, err := app.RabbitMQ.sendRequest(userIDStr)
	if err != nil {
		products, err := database.GetProducts(app.DB)
		if err != nil {
			errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
			http.Error(w, "Failed to get products", http.StatusInternalServerError)
			return
		}
		json.NewEncoder(w).Encode(products)
		return
	}

	response := app.RabbitMQ.receiveResponse(userIDStr, correlationID, queueName)
	if response == "" {
		products, err := database.GetProducts(app.DB)
		if err != nil {
			errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
			http.Error(w, "Failed to get products", http.StatusInternalServerError)
			return
		}
		json.NewEncoder(w).Encode(products)
		return
	}

	var recommendationResponse models.RecommendationResponse
	if err := json.Unmarshal([]byte(response), &recommendationResponse); err != nil {
		products, err := database.GetProducts(app.DB)
		if err != nil {
			errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
			http.Error(w, "Failed to get products", http.StatusInternalServerError)
			return
		}
		json.NewEncoder(w).Encode(products)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(recommendationResponse.Recommendations)
}

// @Summary Delete a product
// @Tags Products
// @Produce json
// @Success 200 {array} string
// @Router /products [delete]
func (app *Application) deleteProduct(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/products/{email}").Inc()

	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/products/{email}"))
	defer timer.ObserveDuration()

	id, err := strconv.Atoi(mux.Vars(r)["id"])
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	err = database.DeleteProduct(app.DB, id)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
		http.Error(w, "Failed delete the product", http.StatusInternalServerError)
		return
	}

	w.Write([]byte("Product was deleted"))
}
