package application

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	database "main/src/db"
	"main/src/models"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/joho/godotenv"

	"github.com/jmoiron/sqlx"
	"github.com/stretchr/testify/assert"
)

func setupTestServer() *Application {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Ошибка загрузки .env файла")
	}

	dbURL := os.Getenv("TEST_DATABASE_URL")
	if dbURL == "" {
		fmt.Println("TEST_DATABASE_URL is not set")
		os.Exit(1)
	}

	app := NewApplication()
	db, err := sqlx.Open("postgres", dbURL)
	if err != nil {
		return nil
	}

	app.DB = db

	app.RegisterHandlers()

	return app
}

func TestCreateProduct(t *testing.T) {
	app := setupTestServer()

	product := models.Product{
		ID:          1,
		Name:        "test",
		Description: "test",
		Price:       10,
		Quantity:    3,
	}

	err := database.CreateProduct(app.DB, product)
	if err != nil {
		return
	}

	reqBody := map[string]interface{}{
		"name":  "Test Product",
		"price": 100,
		"stock": 10,
	}
	jsonBody, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("POST", "/products", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusCreated, resp.Code)
}

func TestGetProducts(t *testing.T) {
	app := setupTestServer()

	product := models.Product{
		ID:          1,
		Name:        "test",
		Description: "test",
		Price:       10,
		Quantity:    3,
	}

	err := database.CreateProduct(app.DB, product)
	if err != nil {
		return
	}

	email := "test@example.com"
	req, _ := http.NewRequest("GET", fmt.Sprintf("/products/%s", email), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
	assert.Contains(t, resp.Body.String(), "products")
}

func TestDeleteProduct(t *testing.T) {
	app := setupTestServer()

	product := models.Product{
		ID:          1,
		Name:        "test",
		Description: "test",
		Price:       10,
		Quantity:    3,
	}

	err := database.CreateProduct(app.DB, product)
	if err != nil {
		return
	}
	email := "test@example.com"
	req, _ := http.NewRequest("DELETE", fmt.Sprintf("/products/%s", email), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
}

func TestAddToOrder(t *testing.T) {
	app := setupTestServer()
	reqBody := map[string]interface{}{
		"email":      "test@example.com",
		"product_id": 1,
		"quantity":   2,
	}
	jsonBody, _ := json.Marshal(reqBody)

	order := models.Order{
		ID:        1,
		Email:     "test@example.com",
		ProductID: 1,
	}

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		return
	}

	req, _ := http.NewRequest("POST", "/order/add", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
}

func TestGetOrder(t *testing.T) {
	app := setupTestServer()

	order := models.Order{
		ID:        1,
		Email:     "test@example.com",
		ProductID: 1,
	}

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		return
	}

	email := "test@example.com"
	req, _ := http.NewRequest("GET", fmt.Sprintf("/order/%s", email), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
	assert.Contains(t, resp.Body.String(), "order")
}

func TestPayForOrder(t *testing.T) {
	app := setupTestServer()

	user := models.User{
		Name:           "test",
		Email:          "test@example.com",
		HashedPassword: "test",
		Balance:        100000,
		CreatedAt:      time.Now(),
	}

	err := database.CreateUser(app.DB, user)
	if err != nil {
		return
	}

	email := "test@example.com"
	req, _ := http.NewRequest("POST", fmt.Sprintf("/order/%s/pay", email), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
}

func TestRemoveFromOrder(t *testing.T) {
	app := setupTestServer()

	order := models.Order{
		ID:        1,
		Email:     "test@example.com",
		ProductID: 1,
	}

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		return
	}

	email := "test@example.com"
	productID := 1
	req, _ := http.NewRequest("DELETE", fmt.Sprintf("/order/%s/%d", email, productID), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
}

func TestClearCart(t *testing.T) {
	app := setupTestServer()

	order := models.Order{
		ID:        1,
		Email:     "test@example.com",
		ProductID: 1,
	}

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		return
	}

	email := "test@example.com"
	req, _ := http.NewRequest("POST", fmt.Sprintf("/order/%s/clear", email), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
}

func TestGetHistoryOrders(t *testing.T) {
	app := setupTestServer()

	order := models.Order{
		ID:        1,
		Email:     "test@example.com",
		ProductID: 1,
	}

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		return
	}

	email := "test@example.com"
	req, _ := http.NewRequest("GET", fmt.Sprintf("/orders/%s/history", email), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
	assert.Contains(t, resp.Body.String(), "history")
}

func TestUpdateProduct(t *testing.T) {
	app := setupTestServer()

	product := models.Product{
		ID:          1,
		Name:        "test",
		Description: "test",
		Price:       10,
		Quantity:    3,
	}

	err := database.CreateProduct(app.DB, product)
	if err != nil {
		return
	}

	reqBody := map[string]interface{}{
		"name":  "Updated Product",
		"price": 150,
		"stock": 5,
	}
	jsonBody, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("PUT", fmt.Sprintf("/products/%d", product.ID), bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
}

func TestUpdateOrder(t *testing.T) {
	app := setupTestServer()

	order := models.Order{
		ID:        1,
		Email:     "test@example.com",
		ProductID: 1,
	}

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		return
	}

	reqBody := map[string]interface{}{
		"quantity": 3,
	}
	jsonBody, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("PUT", fmt.Sprintf("/order/%d", order.ID), bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
}

func TestGetUserDetails(t *testing.T) {
	app := setupTestServer()

	user := models.User{
		Name:           "test",
		Email:          "test@example.com",
		HashedPassword: "test",
		Balance:        100000,
		CreatedAt:      time.Now(),
	}

	err := database.CreateUser(app.DB, user)
	if err != nil {
		return
	}

	req, _ := http.NewRequest("GET", fmt.Sprintf("/user/%s", user.Email), nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)
	assert.Contains(t, resp.Body.String(), "test@example.com")
}

func TestCreateProduct_EmptyValues(t *testing.T) {
	app := setupTestServer()

	reqBody := map[string]interface{}{
		"name":  "test",
		"price": 0,
		"stock": 0,
	}
	jsonBody, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("POST", "/products", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusInternalServerError, resp.Code)
}

func TestAddToOrder_EmptyValues(t *testing.T) {
	app := setupTestServer()

	order := models.Order{
		ID:        1,
		Email:     "test@example.com",
		ProductID: 1,
	}

	err := database.AddProductToOrder(app.DB, order)
	if err != nil {
		return
	}

	reqBody := map[string]interface{}{
		"email":      "test@example.com",
		"product_id": 0,
		"quantity":   0,
	}
	jsonBody, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("POST", "/order/add", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusInternalServerError, resp.Code)
}

func TestPayForOrder_EmptyEmail(t *testing.T) {
	app := setupTestServer()

	req, _ := http.NewRequest("POST", "/order/test_pay", nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusMethodNotAllowed, resp.Code)
}

func TestDeleteProduct_InvalidID(t *testing.T) {
	app := setupTestServer()

	req, _ := http.NewRequest("DELETE", "/products/invalid_id", nil)
	resp := httptest.NewRecorder()

	app.Router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusInternalServerError, resp.Code)
}
