package application

import (
	"log"
	"time"

	"github.com/google/uuid"

	"github.com/streadway/amqp"
)

const (
	requestQueue  = "recommendations"
	responseQueue = "recommendations_response"
	timeout       = 20 * time.Second
)

type RabbitMQ struct {
	channel *amqp.Channel
	replyQueueName string
}

func (r *RabbitMQ) sendRequest(userID string) (string, error) {
	correlationID := uuid.New().String()

	replyQueue, err := r.channel.QueueDeclare(
		"",
		false,
		true,
		true,
		false,
		nil,
	)
	if err != nil {
		return "", err
	}

	err = r.channel.Publish(
		"",
		requestQueue,
		false,
		false,
		amqp.Publishing{
			ContentType:   "application/json",
			Body:         []byte(userID),
			ReplyTo:      replyQueue.Name,
			CorrelationId: correlationID,
		})

	r.replyQueueName = replyQueue.Name
	return correlationID, err
}

func (r *RabbitMQ) receiveResponse(correlationID string) string {
	log.Printf("Waiting for response with correlationID: %s", correlationID)

	msgs, err := r.channel.Consume(
		r.replyQueueName,
		"",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Printf("Failed to register a consumer: %v", err)
		return ""
	}

	select {
	case msg := <-msgs:
		log.Printf("Received response with content type: %s", msg.ContentType)
		return string(msg.Body)
	case <-time.After(timeout):
		log.Printf("Timeout waiting for response from recommendation service")
		return ""
	}
}
