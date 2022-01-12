package database

import (
	"database/sql"
	"fmt"
)

func Connect(host string, port int, user string, password string, database string) (*Queries, error) {
	db, err := sql.Open("postgres", fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable", host, port, user, password, database))
	if err != nil {
		return nil, err
	}
	return New(db), nil
}

var MediaTypeInt = []string{"unknonwn", "tvs_episode", "tvs", "movie", "url", "tvs_season", "movie_collection", "person"}
