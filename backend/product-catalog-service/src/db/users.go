package database

import (
	"main/src/models"
	"time"
)

func UpdateUser(db DB, user models.User) error {
	query := `UPDATE users SET email = :email, hashed_password = :hashed_password, name = :name, balance = :balance, updated_at = :updated_at WHERE id = :id`

	user.UpdatedAt = time.Now()

	_, err := db.NamedExec(query, user)

	return err
}

func GetUser(db DB, userID int) (models.User, error) {
	query := `SELECT id, email, hashed_password, name, balance, created_at, updated_at FROM users WHERE id = $1`

	var user models.User

	err := db.Get(&user, query, userID)
	if err != nil {
		return models.User{}, err
	}

	return user, nil
}
