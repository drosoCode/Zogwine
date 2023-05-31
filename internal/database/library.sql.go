// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.16.0
// source: library.sql

package database

import (
	"context"
)

const getLibrary = `-- name: GetLibrary :one
SELECT id, name, path, media_type FROM library WHERE id = $1
`

func (q *Queries) GetLibrary(ctx context.Context, id int64) (Library, error) {
	row := q.db.QueryRowContext(ctx, getLibrary, id)
	var i Library
	err := row.Scan(
		&i.ID,
		&i.Name,
		&i.Path,
		&i.MediaType,
	)
	return i, err
}

const listLibrary = `-- name: ListLibrary :many
SELECT id, name, path, media_type FROM library
`

func (q *Queries) ListLibrary(ctx context.Context) ([]Library, error) {
	rows, err := q.db.QueryContext(ctx, listLibrary)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Library
	for rows.Next() {
		var i Library
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Path,
			&i.MediaType,
		); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Close(); err != nil {
		return nil, err
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const listLibraryWithType = `-- name: ListLibraryWithType :many
SELECT id, name, path, media_type FROM library WHERE media_type = $1
`

func (q *Queries) ListLibraryWithType(ctx context.Context, mediaType MediaType) ([]Library, error) {
	rows, err := q.db.QueryContext(ctx, listLibraryWithType, mediaType)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Library
	for rows.Next() {
		var i Library
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Path,
			&i.MediaType,
		); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Close(); err != nil {
		return nil, err
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}
