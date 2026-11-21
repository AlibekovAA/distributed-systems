package application

import (
	"context"
	"fmt"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

type authContextKey string

const (
	emailContextKey authContextKey = "email"
	roleContextKey  authContextKey = "role"
)

type tokenClaims struct {
	Type string `json:"type"`
	Role string `json:"role"`
	jwt.RegisteredClaims
}

func (app *Application) authenticate(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		scheme, tokenString, found := strings.Cut(r.Header.Get("Authorization"), " ")
		if !found || !strings.EqualFold(scheme, "Bearer") || tokenString == "" {
			w.Header().Set("WWW-Authenticate", "Bearer")
			writeJSONError(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		claims := &tokenClaims{}
		token, err := jwt.ParseWithClaims(
			tokenString,
			claims,
			func(token *jwt.Token) (any, error) {
				if token.Method.Alg() != app.JWTAlgorithm {
					return nil, fmt.Errorf("unexpected signing algorithm")
				}
				return []byte(app.JWTSecret), nil
			},
			jwt.WithValidMethods([]string{app.JWTAlgorithm}),
		)
		if err != nil || !token.Valid || claims.Subject == "" || claims.Type != "access" {
			w.Header().Set("WWW-Authenticate", "Bearer")
			writeJSONError(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		ctx := context.WithValue(r.Context(), emailContextKey, claims.Subject)
		ctx = context.WithValue(ctx, roleContextKey, claims.Role)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func (app *Application) requireAdmin(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if role, _ := r.Context().Value(roleContextKey).(string); role != "admin" {
			writeJSONError(w, "Forbidden", http.StatusForbidden)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func authenticatedEmail(r *http.Request) string {
	email, _ := r.Context().Value(emailContextKey).(string)
	return email
}

func requireOwnEmail(w http.ResponseWriter, r *http.Request, requestedEmail string) (string, bool) {
	email := authenticatedEmail(r)
	if !strings.EqualFold(email, requestedEmail) {
		writeJSONError(w, "Forbidden", http.StatusForbidden)
		return "", false
	}
	return email, true
}
