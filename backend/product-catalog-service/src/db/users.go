package database

import (
	"main/src/models"
)

func UpdateUser(db DB, user models.User) error {
	query := `UPDATE users SET email = :email, hashed_password = :hashed_password, name = :name, balance = :balance WHERE id = :id`
	_, err := db.NamedExec(query, user)
	return err
}

func GetUser(db DB, userID int64) (models.User, error) {
	query := `SELECT id, email, hashed_password, name, balance, created_at FROM users WHERE id = $1`

	var user models.User

	err := db.Get(&user, query, userID)
	if err != nil {
		return models.User{}, err
	}

	return user, nil
}

func GetUserByEmail(db DB, email string) (models.User, error) {
	query := `SELECT id, email, hashed_password, name, balance, created_at FROM users WHERE email = $1`

	var user models.User
	err := db.Get(&user, query, email)
	if err != nil {
		return models.User{}, err
	}

	return user, nil
}
