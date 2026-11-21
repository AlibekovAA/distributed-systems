package application

import (
	"encoding/json"
	"log"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/streadway/amqp"
)

const (
	requestQueue = "recommendations"
	timeout      = 30 * time.Second
)

type RabbitMQ struct {
	channel *amqp.Channel
}

func (r *RabbitMQ) initializeRequestQueue() error {
	_, err := r.channel.QueueDeclare(
		requestQueue,
		true,
		false,
		false,
		false,
		nil,
	)
	return err
}

func (r *RabbitMQ) sendRequest(userID string, requestID string) (string, string, error) {
	rabbitmqRequestsTotal.WithLabelValues(requestQueue).Inc()

	timer := prometheus.NewTimer(rabbitmqRequestDuration.WithLabelValues(requestQueue))
	defer timer.ObserveDuration()

	err := r.initializeRequestQueue()
	if err != nil {
		rabbitmqErrorsTotal.WithLabelValues(requestQueue).Inc()
		return "", "", err
	}

	tempQueue, err := r.channel.QueueDeclare(
		"",
		false,
		true,
		true,
		false,
		nil,
	)
	if err != nil {
		log.Printf("Failed to create temporary queue: %v", err)
		rabbitmqErrorsTotal.WithLabelValues(requestQueue).Inc()
		return "", "", err
	}

	correlationID := requestID
	if correlationID == "" {
		correlationID = userID + "_" + strconv.FormatInt(time.Now().UnixNano(), 10)
	}
	log.Printf("Sending recommendation request: request_id=%s", correlationID)

	err = r.channel.Publish(
		"",
		requestQueue,
		false,
		false,
		amqp.Publishing{
			ContentType:   "application/json",
			Body:          []byte(userID),
			MessageId:     userID,
			CorrelationId: correlationID,
			ReplyTo:       tempQueue.Name,
		})

	if err != nil {
		rabbitmqErrorsTotal.WithLabelValues(requestQueue).Inc()
		log.Printf("Failed to send request: %v", err)
		r.channel.QueueDelete(tempQueue.Name, false, false, false)
		return "", "", err
	}

	return correlationID, tempQueue.Name, nil
}

func (r *RabbitMQ) receiveResponse(userID string, correlationID string, queueName string) string {
	timer := prometheus.NewTimer(rabbitmqRequestDuration.WithLabelValues(requestQueue))
	defer timer.ObserveDuration()

	log.Printf("Waiting for recommendation response: request_id=%s", correlationID)
	consumerTag := "recommendation-" + newRequestID()

	msgs, err := r.channel.Consume(
		queueName,
		consumerTag,
		true,
		true,
		false,
		false,
		nil,
	)

	if err != nil {
		rabbitmqErrorsTotal.WithLabelValues(requestQueue).Inc()
		log.Printf("Error connecting to response queue: %v", err)
		return ""
	}
	defer r.channel.Cancel(consumerTag, false)

	messageChannel := make(chan string, 1)
	timeoutTimer := time.NewTimer(timeout)
	defer timeoutTimer.Stop()

	go func() {
		for msg := range msgs {
			if msg.CorrelationId != correlationID {
				continue
			}

			var response map[string]interface{}
			if err := json.Unmarshal(msg.Body, &response); err != nil {
				rabbitmqErrorsTotal.WithLabelValues(requestQueue).Inc()
				log.Printf("Error unmarshaling response: %v", err)
				continue
			}

			if responseUserID, ok := response["user_id"].(float64); ok {
				if strconv.FormatFloat(responseUserID, 'f', 0, 64) == userID {
					rabbitmqResponsesTotal.WithLabelValues(requestQueue).Inc()
					messageChannel <- string(msg.Body)
					return
				}
			}
		}
	}()

	select {
	case response := <-messageChannel:
		log.Printf("Received recommendation response: request_id=%s", correlationID)
		return response
	case <-timeoutTimer.C:
		rabbitmqErrorsTotal.WithLabelValues(requestQueue).Inc()
		log.Printf("Recommendation response timeout: request_id=%s", correlationID)
		return ""
	}
}
