FROM golang:1.22 AS builder

WORKDIR /app
COPY go.mod go.sum ./
COPY vendor ./vendor
COPY src ./src
WORKDIR /app/src
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /app/main .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/main .

RUN apk add --no-cache curl netcat-openbsd

EXPOSE 8080 8081
CMD ["/app/main"]
