package application

import (
	"context"
	"log"
	"main/src/config"
	database "main/src/db"
	"net/http"

	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
)

type Application struct {
	DB     database.DB
	Router *mux.Router
	Addr   string
}

func NewApplication() *Application {
	return &Application{
		Router: mux.NewRouter(),
	}
}

func (app *Application) Configure(ctx context.Context, cfg *config.Config) error {
	db, err := database.OpenDB(&cfg.Database)
	if err != nil {

		return err
	}

	app.DB = db

	app.Addr = cfg.Addr

	return nil
}

func (app *Application) Run(ctx context.Context) {

	app.RegisterHandlers()

	err := http.ListenAndServe(app.Addr, app.Router)
	if err != nil {
		log.Fatalf("Ошибка запуска сервера: %v", err)
	}

	log.Printf("Сервер запущен на %s", app.Addr)

}

func (app *Application) RegisterHandlers() {

	// товары
	app.Router.HandleFunc("/products", app.createProduct).Methods("POST")
	app.Router.HandleFunc("/products", app.getProducts).Methods("GET")
	//app.Router.HandleFunc("/products/{id}", updateProduct).Methods("PUT")
	app.Router.HandleFunc("/products/{id}", app.deleteProduct).Methods("DELETE")

	// Корзина
	//app.Router.HandleFunc("/cart/add", addToCart).Methods("POST")
	//app.Router.HandleFunc("/cart/{user_id}", getCart).Methods("GET")
	//app.Router.HandleFunc("/cart/{user_id}/{product_id}", removeFromCart).Methods("DELETE")

	// Баланс
	app.Router.HandleFunc("/users/top-up", app.topUpBalance).Methods("POST")
	//r.HandleFunc("/users/{id}/balance", getBalance).Methods("GET")

	// Заказы
	//r.HandleFunc("/orders/{user_id}", getOrders).Methods("GET")

}
