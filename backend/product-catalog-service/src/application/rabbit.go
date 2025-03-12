package application

import (
	"encoding/json"
	"log"
	"strconv"
	"time"

	"github.com/streadway/amqp"
)

const (
	requestQueue  = "recommendations"
	responseQueue = "recommendations_response"
	timeout       = 10 * time.Second
)

type RabbitMQ struct {
	channel *amqp.Channel
}

func (r *RabbitMQ) sendRequest(userID string) error {
	_, err := r.channel.QueueDeclare(
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

	_, err = r.channel.QueueDeclare(
		responseQueue,
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		return err
	}

	err = r.channel.Publish(
		"",
		requestQueue,
		false,
		false,
		amqp.Publishing{
			ContentType: "application/json",
			Body:       []byte(userID),
			MessageId:  userID,
		})

	if err != nil {
		log.Printf("Failed to send request: %v", err)
		return err
	}

	return nil
}

func (r *RabbitMQ) receiveResponse(userID string) string {
	msgs, err := r.channel.Consume(
		responseQueue,
		"",
		true,
		false,
		false,
		false,
		nil,
	)

	if err != nil {
		log.Printf("Error connecting to response queue: %v", err)
		return ""
	}

	messageChannel := make(chan string)

	go func() {
		for msg := range msgs {
			var response map[string]interface{}
			if err := json.Unmarshal(msg.Body, &response); err != nil {
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
		return response
	case <-time.After(10 * time.Second):
		log.Printf("Timeout waiting for response for user %s", userID)
		return ""
	}
}
