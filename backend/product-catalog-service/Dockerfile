FROM golang:1.22 AS builder

WORKDIR /app

COPY go.mod go.sum ./

COPY vendor ./vendor

COPY src ./src

WORKDIR /app/src

RUN go build -mod=vendor -o /app/main .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /app/main .

FROM alpine:latest  

WORKDIR /app

COPY --from=builder /app/main .

EXPOSE 8080

CMD ["/app/main"]

