package application

import (
	"encoding/json"
	"log"
	"strconv"
	"time"

	"github.com/streadway/amqp"
)

const (
	requestQueue = "recommendations"
	timeout     = 30 * time.Second
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

func (r *RabbitMQ) sendRequest(userID string) (string, string, error) {
	err := r.initializeRequestQueue()
	if err != nil {
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
		return "", "", err
	}

	correlationID := userID + "_" + strconv.FormatInt(time.Now().UnixNano(), 10)
	log.Printf("Sending request for user %s with correlation ID: %s", userID, correlationID)

	err = r.channel.Publish(
		"",
		requestQueue,
		false,
		false,
		amqp.Publishing{
			ContentType:   "application/json",
			Body:         []byte(userID),
			MessageId:    userID,
			CorrelationId: correlationID,
			ReplyTo:      tempQueue.Name,
		})

	if err != nil {
		log.Printf("Failed to send request: %v", err)
		return "", "", err
	}

	return correlationID, tempQueue.Name, nil
}

func (r *RabbitMQ) receiveResponse(userID string, correlationID string, queueName string) string {
	log.Printf("Waiting for response for user %s with correlation ID: %s on queue: %s", userID, correlationID, queueName)

	msgs, err := r.channel.Consume(
		queueName,
		"",
		true,
		true,
		false,
		false,
		nil,
	)

	if err != nil {
		log.Printf("Error connecting to response queue: %v", err)
		return ""
	}

	messageChannel := make(chan string)
	timeoutChannel := time.After(timeout)

	go func() {
		for msg := range msgs {
			log.Printf("Received message with correlation ID: %s, expected: %s", msg.CorrelationId, correlationID)

			if msg.CorrelationId != correlationID {
				log.Printf("Skipping message with wrong correlation ID")
				continue
			}

			var response map[string]interface{}
			if err := json.Unmarshal(msg.Body, &response); err != nil {
				log.Printf("Error unmarshaling response: %v", err)
				continue
			}

			if responseUserID, ok := response["user_id"].(float64); ok {
				if strconv.FormatFloat(responseUserID, 'f', 0, 64) == userID {
					messageChannel <- string(msg.Body)
					return
				}
			}
		}
	}()

	select {
	case response := <-messageChannel:
		log.Printf("Received valid response for user %s", userID)
		return response
	case <-timeoutChannel:
		log.Printf("Timeout waiting for response for user %s", userID)
		return ""
	}
}
