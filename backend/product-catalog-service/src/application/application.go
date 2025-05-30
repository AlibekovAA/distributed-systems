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
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/streadway/amqp"
	httpSwagger "github.com/swaggo/http-swagger"
)

var (
	requestCount = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "product_http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint"},
	)

	requestDuration = prometheus.NewSummaryVec(
		prometheus.SummaryOpts{
			Name: "product_http_request_duration_seconds",
			Help: "Duration of HTTP requests",
		},
		[]string{"method", "endpoint"},
	)

	errorCount = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "product_http_errors_total",
			Help: "Total number of HTTP errors",
		},
		[]string{"method", "endpoint"},
	)

	rabbitmqRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "product_rabbitmq_requests_total",
			Help: "Total number of RabbitMQ requests",
		},
		[]string{"queue"},
	)

	rabbitmqResponsesTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "rabbitmq_responses_total",
			Help: "Total number of RabbitMQ responses",
		},
		[]string{"queue"},
	)

	rabbitmqRequestDuration = prometheus.NewSummaryVec(
		prometheus.SummaryOpts{
			Name: "rabbitmq_request_duration_seconds",
			Help: "Duration of RabbitMQ requests",
		},
		[]string{"queue"},
	)

	rabbitmqErrorsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "rabbitmq_errors_total",
			Help: "Total number of RabbitMQ errors",
		},
		[]string{"queue"},
	)
)

func initMetrics() {
	prometheus.MustRegister(requestCount)
	prometheus.MustRegister(requestDuration)
	prometheus.MustRegister(errorCount)

	prometheus.MustRegister(rabbitmqRequestsTotal)
	prometheus.MustRegister(rabbitmqResponsesTotal)
	prometheus.MustRegister(rabbitmqRequestDuration)
	prometheus.MustRegister(rabbitmqErrorsTotal)
}

type Application struct {
	DB            database.DB
	Router        *mux.Router
	Addr          string
	RabbitConn    *amqp.Connection
	RabbitChannel *amqp.Channel
	RabbitMQ      *RabbitMQ
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

	conn, err := amqp.Dial(cfg.RabbitMQURL)
	if err != nil {
		log.Fatalf("Failed to connect to RabbitMQ %+v", err)
	}

	app.RabbitConn = conn

	ch, err := conn.Channel()
	if err != nil {
		log.Fatalf("Failed to open a channel %+v", err)
	}

	app.RabbitChannel = ch

	app.RabbitMQ = &RabbitMQ{
		channel: app.RabbitChannel,
	}

	return nil
}

func (app *Application) Run(ctx context.Context) {
	initMetrics()
	app.RegisterHandlers()

	go func() {
		log.Println("Starting metrics server on :8081")
		if err := http.ListenAndServe(":8081", promhttp.Handler()); err != nil {
			log.Printf("Failed to start metrics server: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	serverErr := make(chan error, 1)

	go func() {
		log.Printf("Product-catalog-service running on  %s", app.Addr)
		serverErr <- http.ListenAndServe(app.Addr, corsMiddleware(app.Router))
	}()

	select {
	case err := <-serverErr:
		if err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed start product-catalog-service: %v", err)
		}
	case <-stop:
		log.Println("Shutting down the product-catalog-service...")
	}

	if app.RabbitChannel != nil {
		log.Println("Closing RabbitMQ channel...")
		app.RabbitChannel.Close()
	}
	if app.RabbitConn != nil {
		log.Println("Closing RabbitMQ connection...")
		app.RabbitConn.Close()
	}

	shutdownCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	<-shutdownCtx.Done()

	log.Println("The product-catalog-service is terminated correctly")
}

// @title Online Store API
// @version 1.0
// @description API for managing goods and orders
// @host localhost:8080
// @BasePath /
func (app *Application) RegisterHandlers() {
	//метрики
	app.Router.Handle("/metrics", promhttp.Handler())
	// товары
	app.Router.HandleFunc("/products/{email}", app.getProducts).Methods("GET")
	//app.Router.HandleFunc("/products/{id}", updateProduct).Methods("PUT")
	app.Router.HandleFunc("/products", app.createProduct).Methods("POST")
	app.Router.HandleFunc("/products/{email}", app.deleteProduct).Methods("DELETE")

	// Заказ (корзина)
	app.Router.HandleFunc("/order/add", app.addToOrder).Methods("POST")
	app.Router.HandleFunc("/order/{email}", app.getOrder).Methods("GET")
	app.Router.HandleFunc("/order/{email}/pay", app.payForOrder).Methods("POST")
	app.Router.HandleFunc("/order/{email}/{product_id}", app.removeFromOrder).Methods("DELETE")
	app.Router.HandleFunc("/order/{email}/clear", app.clearCart).Methods("POST")

	// История заказов
	app.Router.HandleFunc("/orders/{email}/history", app.getHistoryOrders).Methods("GET")

	app.Router.PathPrefix("/swagger/").Handler(httpSwagger.WrapHandler)

}

func corsMiddleware(next http.Handler) http.Handler {
	allowedOrigins := map[string]bool{
		"http://localhost":		true,
		"http://localhost:80":	true,
		"http://frontend":		true,
		"http://nginx":			true,
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if allowedOrigins[origin] {
			w.Header().Set("Access-Control-Allow-Origin", origin)
		}

		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Access-Control-Allow-Credentials", "true")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
