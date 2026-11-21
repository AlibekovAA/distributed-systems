package application

import (
	"context"
	"fmt"
	"log"
	"main/src/config"
	database "main/src/db"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/streadway/amqp"
	httpSwagger "github.com/swaggo/http-swagger"
)

var metricsOnce sync.Once

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
	metricsOnce.Do(func() {
		prometheus.MustRegister(requestCount)
		prometheus.MustRegister(requestDuration)
		prometheus.MustRegister(errorCount)
		prometheus.MustRegister(rabbitmqRequestsTotal)
		prometheus.MustRegister(rabbitmqResponsesTotal)
		prometheus.MustRegister(rabbitmqRequestDuration)
		prometheus.MustRegister(rabbitmqErrorsTotal)
	})
}

type Application struct {
	DB            database.DB
	Router        *mux.Router
	Addr          string
	RabbitConn    *amqp.Connection
	RabbitChannel *amqp.Channel
	RabbitMQ      *RabbitMQ
	JWTSecret     string
	JWTAlgorithm  string
}

func NewApplication() *Application {
	return &Application{
		Router: mux.NewRouter(),
	}
}

func (app *Application) Configure(ctx context.Context, cfg *config.Config) error {
	db, err := database.OpenDB(&cfg.Database)
	if err != nil {
		return fmt.Errorf("open database: %w", err)
	}
	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return fmt.Errorf("ping database: %w", err)
	}

	app.DB = db
	app.Addr = cfg.Addr
	app.JWTSecret = cfg.JWTSecret
	app.JWTAlgorithm = cfg.JWTAlgorithm

	conn, err := amqp.Dial(cfg.RabbitMQURL)
	if err != nil {
		db.Close()
		return fmt.Errorf("connect to RabbitMQ: %w", err)
	}

	app.RabbitConn = conn

	ch, err := conn.Channel()
	if err != nil {
		conn.Close()
		db.Close()
		return fmt.Errorf("open RabbitMQ channel: %w", err)
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
	apiServer := &http.Server{Addr: app.Addr, Handler: corsMiddleware(app.Router), ReadHeaderTimeout: 5 * time.Second}
	metricsServer := &http.Server{Addr: ":8081", Handler: promhttp.Handler(), ReadHeaderTimeout: 5 * time.Second}
	serverErr := make(chan error, 2)

	go func() {
		log.Println("Starting metrics server on :8081")
		if err := metricsServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			serverErr <- fmt.Errorf("metrics server: %w", err)
		}
	}()

	go func() {
		log.Printf("Product-catalog-service running on %s", app.Addr)
		if err := apiServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			serverErr <- fmt.Errorf("API server: %w", err)
		}
	}()

	stopCtx, stop := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
	defer stop()
	select {
	case err := <-serverErr:
		log.Printf("Product-catalog-service stopped unexpectedly: %v", err)
	case <-stopCtx.Done():
		log.Println("Shutting down product-catalog-service")
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := apiServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("API server shutdown failed: %v", err)
	}
	if err := metricsServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("Metrics server shutdown failed: %v", err)
	}
	if app.RabbitChannel != nil {
		if err := app.RabbitChannel.Close(); err != nil {
			log.Printf("RabbitMQ channel close failed: %v", err)
		}
	}
	if app.RabbitConn != nil {
		if err := app.RabbitConn.Close(); err != nil {
			log.Printf("RabbitMQ connection close failed: %v", err)
		}
	}
	if app.DB != nil {
		if err := app.DB.Close(); err != nil {
			log.Printf("Database close failed: %v", err)
		}
	}
	log.Println("Product-catalog-service stopped")
}

// @title Online Store API
// @version 1.0
// @description API for managing goods and orders
// @host localhost:8080
// @BasePath /
// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization
func (app *Application) RegisterHandlers() {
	app.Router.Use(requestIDMiddleware)
	app.Router.NotFoundHandler = http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		writeJSONError(w, "Not found", http.StatusNotFound)
	})
	app.Router.MethodNotAllowedHandler = http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		writeJSONError(w, "Method not allowed", http.StatusMethodNotAllowed)
	})
	//метрики
	app.Router.Handle("/metrics", promhttp.Handler())

	protected := app.Router.NewRoute().Subrouter()
	protected.Use(app.authenticate)

	// товары
	protected.HandleFunc("/products/{email}", app.getProducts).Methods("GET")
	protected.Handle("/products", app.requireAdmin(http.HandlerFunc(app.createProduct))).Methods("POST")
	protected.Handle("/products/{id}", app.requireAdmin(http.HandlerFunc(app.deleteProduct))).Methods("DELETE")

	// Заказ (корзина)
	protected.HandleFunc("/order/add", app.addToOrder).Methods("POST")
	protected.HandleFunc("/order/{email}", app.getOrder).Methods("GET")
	protected.HandleFunc("/order/{email}/pay", app.payForOrder).Methods("POST")
	protected.HandleFunc("/order/{email}/{product_id}", app.removeFromOrder).Methods("DELETE")
	protected.HandleFunc("/order/{email}/clear", app.clearCart).Methods("POST")

	// История заказов
	protected.HandleFunc("/orders/{email}/history", app.getHistoryOrders).Methods("GET")

	protected.PathPrefix("/swagger/").Handler(httpSwagger.WrapHandler)

}

func corsMiddleware(next http.Handler) http.Handler {
	allowedOrigins := map[string]bool{
		"http://localhost":    true,
		"http://localhost:80": true,
		"http://frontend":     true,
		"http://nginx":        true,
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if allowedOrigins[origin] {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
			w.Header().Set("Access-Control-Allow-Credentials", "true")
		}

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
