package application

import (
	"log"

	"github.com/streadway/amqp"
)

const (
	requestQueue  = "recommendations"
	responseQueue = "recommendations_response"
)

func sendRequest(ch *amqp.Channel, userID string) error {
	return ch.Publish(
		"", requestQueue, false, false,
		amqp.Publishing{
			ContentType:   "text/plain",
			Body:          []byte(userID),
			ReplyTo:       responseQueue,
			CorrelationId: userID,
		})
}

func receiveResponse(ch *amqp.Channel) string {
	msgs, err := ch.Consume(
		responseQueue, "", true, false, false, false, nil,
	)
	if err != nil {
		log.Fatalf("Failed to register a consumer %+v", err)
	}

	for msg := range msgs {
		return string(msg.Body)
	}
	return ""
}
