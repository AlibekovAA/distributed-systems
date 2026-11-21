package application

import (
	"bytes"
	"encoding/json"
	"errors"
	database "main/src/db"
	"main/src/models"
	"net/http"
	"net/http/httptest"
	"strconv"
	"sync"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const testEmail = "test@example.com"

func setupTestServer(t *testing.T) *Application {
	t.Helper()

	db, err := sqlx.Open("postgres", "postgresql://test_user:test_password@postgres-test:5432/test_db?sslmode=disable")
	require.NoError(t, err)
	require.NoError(t, db.Ping())
	t.Cleanup(func() { require.NoError(t, db.Close()) })

	_, err = db.Exec(`TRUNCATE TABLE history, "order", user_order_counters, user_preferences, product, users RESTART IDENTITY CASCADE`)
	require.NoError(t, err)

	app := NewApplication()
	app.DB = db
	app.JWTSecret = "test-secret"
	app.JWTAlgorithm = "HS256"
	app.RegisterHandlers()
	return app
}

func authorizeRequest(t *testing.T, request *http.Request, email string, role string) {
	t.Helper()
	claims := tokenClaims{
		Type: "access",
		Role: role,
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   email,
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
		},
	}
	token, err := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString([]byte("test-secret"))
	require.NoError(t, err)
	request.Header.Set("Authorization", "Bearer "+token)
}

func createTestUser(t *testing.T, app *Application, balance int) models.User {
	t.Helper()
	user := models.User{Name: "Test", Email: testEmail, HashedPassword: "hash", Balance: balance}
	require.NoError(t, database.CreateUser(app.DB, user))
	created, err := database.GetUserByEmail(app.DB, testEmail)
	require.NoError(t, err)
	return created
}

func createTestProduct(t *testing.T, app *Application, price int64, quantity int) models.Product {
	t.Helper()
	var product models.Product
	err := app.DB.Get(&product, `
		INSERT INTO product (name, description, price, quantity)
		VALUES ('Test product', 'Description', $1, $2)
		RETURNING id, name, description, price, quantity`, price, quantity)
	require.NoError(t, err)
	return product
}

func TestProtectedRouteRequiresToken(t *testing.T) {
	app := setupTestServer(t)
	request := httptest.NewRequest(http.MethodGet, "/products/"+testEmail, nil)
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	assert.Equal(t, http.StatusUnauthorized, response.Code)
	assert.Equal(t, "application/json", response.Header().Get("Content-Type"))
}

func TestProtectedRouteRejectsOtherUser(t *testing.T) {
	app := setupTestServer(t)
	request := httptest.NewRequest(http.MethodGet, "/products/other@example.com", nil)
	authorizeRequest(t, request, testEmail, "user")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	assert.Equal(t, http.StatusForbidden, response.Code)
}

func TestProductChangesRequireAdmin(t *testing.T) {
	app := setupTestServer(t)
	request := httptest.NewRequest(http.MethodPost, "/products", bytes.NewBufferString(`{"name":"test","price":1,"quantity":1}`))
	authorizeRequest(t, request, testEmail, "user")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	assert.Equal(t, http.StatusForbidden, response.Code)
}

func TestCreateProduct(t *testing.T) {
	app := setupTestServer(t)
	body := bytes.NewBufferString(`{"name":"New product","description":"Description","price":100,"quantity":10}`)
	request := httptest.NewRequest(http.MethodPost, "/products", body)
	authorizeRequest(t, request, "admin@example.com", "admin")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	require.Equal(t, http.StatusCreated, response.Code)
	var count int
	require.NoError(t, app.DB.Get(&count, `SELECT COUNT(*) FROM product WHERE name = 'New product'`))
	assert.Equal(t, 1, count)
}

func TestGetProductsFallsBackWhenRabbitMQIsUnavailable(t *testing.T) {
	app := setupTestServer(t)
	createTestUser(t, app, 0)
	product := createTestProduct(t, app, 100, 3)
	request := httptest.NewRequest(http.MethodGet, "/products/"+testEmail, nil)
	authorizeRequest(t, request, testEmail, "user")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	require.Equal(t, http.StatusOK, response.Code)
	var products []models.Product
	require.NoError(t, json.Unmarshal(response.Body.Bytes(), &products))
	require.Len(t, products, 1)
	assert.Equal(t, product.ID, products[0].ID)
}

func TestAddToOrderReservesStock(t *testing.T) {
	app := setupTestServer(t)
	createTestUser(t, app, 0)
	product := createTestProduct(t, app, 100, 2)
	body := bytes.NewBufferString(`{"product_id":` + jsonNumber(product.ID) + `}`)
	request := httptest.NewRequest(http.MethodPost, "/order/add", body)
	authorizeRequest(t, request, testEmail, "user")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	require.Equal(t, http.StatusCreated, response.Code)
	assertProductQuantity(t, app, product.ID, 1)
	assertCartSize(t, app, 1)
}

func TestConcurrentReservationAllowsOnlyAvailableStock(t *testing.T) {
	app := setupTestServer(t)
	createTestUser(t, app, 0)
	product := createTestProduct(t, app, 100, 1)

	errorsChannel := make(chan error, 2)
	var waitGroup sync.WaitGroup
	for i := 0; i < 2; i++ {
		waitGroup.Add(1)
		go func() {
			defer waitGroup.Done()
			errorsChannel <- database.AddProductToOrder(app.DB, models.Order{Email: testEmail, ProductID: product.ID})
		}()
	}
	waitGroup.Wait()
	close(errorsChannel)

	successes := 0
	outOfStock := 0
	for err := range errorsChannel {
		if err == nil {
			successes++
		} else if errors.Is(err, database.ErrProductOutOfStock) {
			outOfStock++
		} else {
			require.NoError(t, err)
		}
	}
	assert.Equal(t, 1, successes)
	assert.Equal(t, 1, outOfStock)
	assertProductQuantity(t, app, product.ID, 0)
	assertCartSize(t, app, 1)
}

func TestRemoveFromOrderRestoresStock(t *testing.T) {
	app := setupTestServer(t)
	createTestUser(t, app, 0)
	product := createTestProduct(t, app, 100, 2)
	require.NoError(t, database.AddProductToOrder(app.DB, models.Order{Email: testEmail, ProductID: product.ID}))
	request := httptest.NewRequest(http.MethodDelete, "/order/"+testEmail+"/"+jsonNumber(product.ID), nil)
	authorizeRequest(t, request, testEmail, "user")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	require.Equal(t, http.StatusOK, response.Code)
	assertProductQuantity(t, app, product.ID, 2)
	assertCartSize(t, app, 0)
}

func TestClearCartRestoresStock(t *testing.T) {
	app := setupTestServer(t)
	createTestUser(t, app, 0)
	product := createTestProduct(t, app, 100, 3)
	require.NoError(t, database.AddProductToOrder(app.DB, models.Order{Email: testEmail, ProductID: product.ID}))
	require.NoError(t, database.AddProductToOrder(app.DB, models.Order{Email: testEmail, ProductID: product.ID}))
	request := httptest.NewRequest(http.MethodPost, "/order/"+testEmail+"/clear", nil)
	authorizeRequest(t, request, testEmail, "user")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	require.Equal(t, http.StatusOK, response.Code)
	assertProductQuantity(t, app, product.ID, 3)
	assertCartSize(t, app, 0)
}

func TestCheckoutUpdatesAllStateAtomically(t *testing.T) {
	app := setupTestServer(t)
	user := createTestUser(t, app, 1000)
	product := createTestProduct(t, app, 100, 5)
	require.NoError(t, database.AddProductToOrder(app.DB, models.Order{Email: testEmail, ProductID: product.ID}))
	request := httptest.NewRequest(http.MethodPost, "/order/"+testEmail+"/pay", bytes.NewBufferString(`{}`))
	authorizeRequest(t, request, testEmail, "user")
	response := httptest.NewRecorder()

	app.Router.ServeHTTP(response, request)

	require.Equal(t, http.StatusOK, response.Code)
	var balance int
	require.NoError(t, app.DB.Get(&balance, `SELECT balance FROM users WHERE id = $1`, user.ID))
	assert.Equal(t, 900, balance)
	assertCartSize(t, app, 0)
	var historyCount int
	require.NoError(t, app.DB.Get(&historyCount, `SELECT COUNT(*) FROM history WHERE user_id = $1`, user.ID))
	assert.Equal(t, 1, historyCount)
	assertProductQuantity(t, app, product.ID, 4)
}

func TestConcurrentCheckoutChargesOnlyOnce(t *testing.T) {
	app := setupTestServer(t)
	user := createTestUser(t, app, 1000)
	product := createTestProduct(t, app, 100, 5)
	require.NoError(t, database.AddProductToOrder(app.DB, models.Order{Email: testEmail, ProductID: product.ID}))

	errorsChannel := make(chan error, 2)
	var waitGroup sync.WaitGroup
	for i := 0; i < 2; i++ {
		waitGroup.Add(1)
		go func() {
			defer waitGroup.Done()
			_, err := database.Checkout(app.DB, testEmail)
			errorsChannel <- err
		}()
	}
	waitGroup.Wait()
	close(errorsChannel)

	successes := 0
	notFound := 0
	for err := range errorsChannel {
		if err == nil {
			successes++
		} else if errors.Is(err, database.ErrOrderNotFound) {
			notFound++
		} else {
			require.NoError(t, err)
		}
	}
	assert.Equal(t, 1, successes)
	assert.Equal(t, 1, notFound)
	var balance int
	require.NoError(t, app.DB.Get(&balance, `SELECT balance FROM users WHERE id = $1`, user.ID))
	assert.Equal(t, 900, balance)
}

func assertProductQuantity(t *testing.T, app *Application, productID int64, expected int) {
	t.Helper()
	var quantity int
	require.NoError(t, app.DB.Get(&quantity, `SELECT quantity FROM product WHERE id = $1`, productID))
	assert.Equal(t, expected, quantity)
}

func assertCartSize(t *testing.T, app *Application, expected int) {
	t.Helper()
	var count int
	require.NoError(t, app.DB.Get(&count, `SELECT COUNT(*) FROM "order" WHERE email = $1`, testEmail))
	assert.Equal(t, expected, count)
}

func jsonNumber(value int64) string {
	return strconv.FormatInt(value, 10)
}
