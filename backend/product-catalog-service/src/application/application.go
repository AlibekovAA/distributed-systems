package application

import (
	"context"
	"log"
	"main/src/config"
	database "main/src/db"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
	httpSwagger "github.com/swaggo/http-swagger"
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

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	serverErr := make(chan error, 1)

	go func() {
		log.Printf("Product-catalog-service running on  %s", app.Addr)
		serverErr <- http.ListenAndServe(app.Addr, app.Router)
	}()

	select {
	case err := <-serverErr:
		if err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed start product-catalog-service: %v", err)
		}
	case <-stop:
		log.Println("Shutting down the product-catalog-service...")
	}

	shutdownCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	<-shutdownCtx.Done()

	log.Println("The product-catalog-service is terminated correctly")
}

// @title Online Store API
// @version 1.0
// @description API для управления товарами и заказами
// @host localhost:8080
// @BasePath /
func (app *Application) RegisterHandlers() {
	// товары
	app.Router.HandleFunc("/products", app.getProducts).Methods("GET")
	//app.Router.HandleFunc("/products/{id}", updateProduct).Methods("PUT")
	app.Router.HandleFunc("/products", app.createProduct).Methods("POST")
	//app.Router.HandleFunc("/products/{id}", app.deleteProduct).Methods("DELETE")

	// Заказ (корзина)
	app.Router.HandleFunc("/order/add", app.addToOrder).Methods("POST")
	app.Router.HandleFunc("/order/{user_id}", app.getOrder).Methods("GET")
	app.Router.HandleFunc("/order/{user_id}/pay", app.payForOrder).Methods("POST")
	app.Router.HandleFunc("/order/{user_id}/{product_id}", app.removeFromOrder).Methods("DELETE")

	app.Router.HandleFunc("/users/{id}/balance", app.getBalance).Methods("GET")

	// История заказов
	app.Router.HandleFunc("/orders/{user_id}/history", app.getHistoryOrders).Methods("GET")

	app.Router.PathPrefix("/swagger/").Handler(httpSwagger.WrapHandler)
}
