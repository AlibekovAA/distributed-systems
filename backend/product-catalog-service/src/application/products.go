package application

import (
	"encoding/json"
	"fmt"
	"log"
	database "main/src/db"
	"main/src/models"
	"net/http"
	"strconv"
	"time"

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
// @Success 200 {array} string
// @Router /products/{user_id} [get]
func (app *Application) getProducts(w http.ResponseWriter, r *http.Request) {
	userID, err := strconv.Atoi(mux.Vars(r)["user_id"])
	if err != nil {
		http.Error(w, "Failed get id", http.StatusInternalServerError)
	}

	_, err = app.RabbitChannel.QueueDeclare(
		responseQueue, false, false, false, false, nil,
	)

	if err != nil {
		log.Printf("Failed to declare a response queue %+v", err)
	}

	err = sendRequest(app.RabbitChannel, strconv.Itoa(userID))

	if err != nil {
		log.Printf("Failed to send request %+v", err)
	}

	response := receiveResponse(app.RabbitChannel)
	fmt.Println("Received response:", response)

	//TODO: сервис рекомендация вернет сюда для каждого юзера рекомендуемые продукты
	//После этого выпилить получение продуктов из бд
	var products []models.Product
	products, err = database.GetProducts(app.DB)
	if err != nil {
		http.Error(w, "Failed get products", http.StatusInternalServerError)
		return
	}

	time.Sleep(20 * time.Second)

	json.NewEncoder(w).Encode(products)
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
