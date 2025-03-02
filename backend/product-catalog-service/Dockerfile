FROM golang:1.22-alpine

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN apk add --no-cache bash

RUN CGO_ENABLED=0 GOOS=linux go build -o /app/main ./src/main.go

EXPOSE 8080

CMD ["/app/main"]
