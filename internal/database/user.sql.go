// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.13.0
// source: user.sql

package database

import (
	"context"
)

const getUser = `-- name: GetUser :one
SELECT id, name, username, enabled FROM "user" WHERE id = $1
`

type GetUserRow struct {
	ID       int64  `json:"id"`
	Name     string `json:"name"`
	Username string `json:"username"`
	Enabled  bool   `json:"enabled"`
}

func (q *Queries) GetUser(ctx context.Context, id int64) (GetUserRow, error) {
	row := q.db.QueryRowContext(ctx, getUser, id)
	var i GetUserRow
	err := row.Scan(
		&i.ID,
		&i.Name,
		&i.Username,
		&i.Enabled,
	)
	return i, err
}

const getUserLoginFromUsername = `-- name: GetUserLoginFromUsername :one
SELECT id, password FROM "user" WHERE username = $1 AND enabled = true LIMIT 1
`

type GetUserLoginFromUsernameRow struct {
	ID       int64  `json:"id"`
	Password string `json:"password"`
}

func (q *Queries) GetUserLoginFromUsername(ctx context.Context, username string) (GetUserLoginFromUsernameRow, error) {
	row := q.db.QueryRowContext(ctx, getUserLoginFromUsername, username)
	var i GetUserLoginFromUsernameRow
	err := row.Scan(&i.ID, &i.Password)
	return i, err
}

const listGroupFromUser = `-- name: ListGroupFromUser :many
SELECT g.name AS name FROM "group" g INNER JOIN group_link l ON (g.id = l.id_group) INNER JOIN "user" u ON (u.id = l.id_user) WHERE u.id = $1 AND g.system = $2
`

type ListGroupFromUserParams struct {
	ID     int64 `json:"id"`
	System bool  `json:"system"`
}

func (q *Queries) ListGroupFromUser(ctx context.Context, arg ListGroupFromUserParams) ([]string, error) {
	rows, err := q.db.QueryContext(ctx, listGroupFromUser, arg.ID, arg.System)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []string
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return nil, err
		}
		items = append(items, name)
	}
	if err := rows.Close(); err != nil {
		return nil, err
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}
