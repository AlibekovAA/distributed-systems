package database

import (
	"main/src/models"
)

func CreateUser(db DB, user models.User) error {
	tx, err := db.Beginx()
	if err != nil {
		return err
	}

	query := `INSERT INTO users (name, email, hashed_password, balance) VALUES ($1, $2, $3, $4) RETURNING id`

	err = tx.QueryRowx(query, user.Name, user.Email, user.HashedPassword, user.Balance).Scan(&user.ID)
	if err != nil {
		tx.Rollback()
		return err
	}

	return tx.Commit()
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
