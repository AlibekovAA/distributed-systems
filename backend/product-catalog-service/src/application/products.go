package application

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	database "main/src/db"
	"main/src/models"
	"net/http"
	"strconv"
	"strings"
	"unicode/utf8"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
)

// @Summary Create a new product
// @Tags Products
// @Produce json
// @Security BearerAuth
// @Success 201
// @Router /products [post]
func (app *Application) createProduct(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/products").Inc()
	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/products"))
	defer timer.ObserveDuration()

	var product models.Product
	if !decodeJSONBody(w, r, &product) {
		errorCount.WithLabelValues(r.Method, "/products").Inc()
		return
	}
	if err := validateProduct(product); err != nil {
		errorCount.WithLabelValues(r.Method, "/products").Inc()
		writeJSONError(w, err.Error(), http.StatusBadRequest)
		return
	}

	err := database.CreateProduct(app.DB, product)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products").Inc()
		writeJSONError(w, "Failed create product", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(product)
}

// @Summary Get a list of products
// @Tags Products
// @Produce json
// @Security BearerAuth
// @Param email path string true "User email"
// @Success 200 {array} string
// @Router /products/{email} [get]
func (app *Application) getProducts(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/products/{email}").Inc()

	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/products/{email}"))
	defer timer.ObserveDuration()

	email, ok := requireOwnEmail(w, r, mux.Vars(r)["email"])
	if !ok {
		errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
		return
	}

	user, err := database.GetUserByEmail(app.DB, email)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
		if errors.Is(err, sql.ErrNoRows) {
			writeJSONError(w, "User not found", http.StatusNotFound)
		} else {
			writeJSONError(w, "Failed to get user", http.StatusInternalServerError)
		}
		return
	}

	userIDStr := strconv.Itoa(int(user.ID))
	if app.RabbitMQ == nil {
		app.writeFallbackProducts(w, r)
		return
	}

	correlationID, queueName, err := app.RabbitMQ.sendRequest(userIDStr, requestIDFromContext(r.Context()))
	if err != nil {
		app.writeFallbackProducts(w, r)
		return
	}

	response := app.RabbitMQ.receiveResponse(userIDStr, correlationID, queueName)
	if response == "" {
		app.writeFallbackProducts(w, r)
		return
	}

	var recommendationResponse models.RecommendationResponse
	if err := json.Unmarshal([]byte(response), &recommendationResponse); err != nil {
		app.writeFallbackProducts(w, r)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(recommendationResponse.Recommendations)
}

func (app *Application) writeFallbackProducts(w http.ResponseWriter, r *http.Request) {
	products, err := database.GetProducts(app.DB)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products/{email}").Inc()
		writeJSONError(w, "Failed to get products", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(products)
}

// @Summary Delete a product
// @Tags Products
// @Produce json
// @Security BearerAuth
// @Param id path int true "Product ID"
// @Success 200 {array} string
// @Router /products/{id} [delete]
func (app *Application) deleteProduct(w http.ResponseWriter, r *http.Request) {
	requestCount.WithLabelValues(r.Method, "/products/{id}").Inc()

	timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, "/products/{id}"))
	defer timer.ObserveDuration()

	id, err := strconv.Atoi(mux.Vars(r)["id"])
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products/{id}").Inc()
		writeJSONError(w, "Invalid product id", http.StatusBadRequest)
		return
	}
	if id <= 0 {
		errorCount.WithLabelValues(r.Method, "/products/{id}").Inc()
		writeJSONError(w, "Product id must be positive", http.StatusBadRequest)
		return
	}

	err = database.DeleteProduct(app.DB, id)
	if err != nil {
		errorCount.WithLabelValues(r.Method, "/products/{id}").Inc()
		if errors.Is(err, sql.ErrNoRows) {
			writeJSONError(w, "Product not found", http.StatusNotFound)
		} else {
			writeJSONError(w, "Failed delete the product", http.StatusInternalServerError)
		}
		return
	}

	w.Write([]byte("Product was deleted"))
}

func validateProduct(product models.Product) error {
	name := strings.TrimSpace(product.Name)
	if length := utf8.RuneCountInString(name); length < 1 || length > 255 {
		return fmt.Errorf("product name must contain between 1 and 255 characters")
	}
	if utf8.RuneCountInString(product.Description) > 10000 {
		return fmt.Errorf("product description must not exceed 10000 characters")
	}
	if product.Price < 1 || product.Price > 1000000000 {
		return fmt.Errorf("product price must be between 1 and 1000000000")
	}
	if product.Quantity < 0 || product.Quantity > 1000000 {
		return fmt.Errorf("product quantity must be between 0 and 1000000")
	}
	return nil
}
