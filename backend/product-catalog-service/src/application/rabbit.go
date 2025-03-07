package application

import (
	"log"
	"time"

	"github.com/streadway/amqp"
)

const (
	requestQueue  = "recommendations"
	responseQueue = "recommendations_response"
)

func sendRequest(ch *amqp.Channel, userID string) error {
	_, err := ch.QueueDeclare(
		requestQueue,
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		return err
	}

	return ch.Publish(
		"",
		requestQueue,
		false,
		false,
		amqp.Publishing{
			ContentType:   "text/plain",
			Body:         []byte(userID),
			DeliveryMode: amqp.Persistent,
		})
}

func receiveResponse(ch *amqp.Channel) string {
	q, err := ch.QueueDeclare(
		responseQueue,
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Printf("Failed to declare a queue: %v", err)
		return ""
	}

	msgs, err := ch.Consume(
		q.Name,
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
		return string(msg.Body)
	case <-time.After(5 * time.Second):
		log.Printf("Timeout waiting for response from recommendation service")
		return ""
	}
}
