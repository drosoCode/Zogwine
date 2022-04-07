// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.13.0
// source: scraper.sql

package database

import (
	"context"
	"encoding/json"

	"github.com/lib/pq"
)

const addMultipleResults = `-- name: AddMultipleResults :exec
INSERT INTO selection (media_type, media_data, data, name) VALUES ($1, $2, $3, $4)
`

type AddMultipleResultsParams struct {
	MediaType MediaType       `json:"mediaType"`
	MediaData int64           `json:"mediaData"`
	Data      json.RawMessage `json:"data"`
	Name      string          `json:"name"`
}

func (q *Queries) AddMultipleResults(ctx context.Context, arg AddMultipleResultsParams) error {
	_, err := q.db.ExecContext(ctx, addMultipleResults,
		arg.MediaType,
		arg.MediaData,
		arg.Data,
		arg.Name,
	)
	return err
}

const deleteMultipleResultsByMedia = `-- name: DeleteMultipleResultsByMedia :exec
DELETE FROM selection WHERE media_type = $1 AND media_data = $2
`

type DeleteMultipleResultsByMediaParams struct {
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) DeleteMultipleResultsByMedia(ctx context.Context, arg DeleteMultipleResultsByMediaParams) error {
	_, err := q.db.ExecContext(ctx, deleteMultipleResultsByMedia, arg.MediaType, arg.MediaData)
	return err
}

const getMultipleResultsByMedia = `-- name: GetMultipleResultsByMedia :one
SELECT media_type, media_data, data, name FROM selection WHERE media_type = $1 AND media_data = $2 LIMIT 1
`

type GetMultipleResultsByMediaParams struct {
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) GetMultipleResultsByMedia(ctx context.Context, arg GetMultipleResultsByMediaParams) (Selection, error) {
	row := q.db.QueryRowContext(ctx, getMultipleResultsByMedia, arg.MediaType, arg.MediaData)
	var i Selection
	err := row.Scan(
		&i.MediaType,
		&i.MediaData,
		&i.Data,
		&i.Name,
	)
	return i, err
}

const listMultipleResults = `-- name: ListMultipleResults :many
SELECT media_type, media_data, data, name FROM selection
`

func (q *Queries) ListMultipleResults(ctx context.Context) ([]Selection, error) {
	rows, err := q.db.QueryContext(ctx, listMultipleResults)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Selection
	for rows.Next() {
		var i Selection
		if err := rows.Scan(
			&i.MediaType,
			&i.MediaData,
			&i.Data,
			&i.Name,
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

const listMultipleResultsByMediaType = `-- name: ListMultipleResultsByMediaType :many
SELECT media_type, media_data, data, name FROM selection WHERE media_type = $1
`

func (q *Queries) ListMultipleResultsByMediaType(ctx context.Context, mediaType MediaType) ([]Selection, error) {
	rows, err := q.db.QueryContext(ctx, listMultipleResultsByMediaType, mediaType)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Selection
	for rows.Next() {
		var i Selection
		if err := rows.Scan(
			&i.MediaType,
			&i.MediaData,
			&i.Data,
			&i.Name,
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

const listScraperForType = `-- name: ListScraperForType :many
SELECT provider, priority, media_type, settings, enabled FROM scraper WHERE $1::media_type = ANY(media_type) ORDER BY priority
`

func (q *Queries) ListScraperForType(ctx context.Context, mediaType MediaType) ([]Scraper, error) {
	rows, err := q.db.QueryContext(ctx, listScraperForType, mediaType)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Scraper
	for rows.Next() {
		var i Scraper
		if err := rows.Scan(
			&i.Provider,
			&i.Priority,
			pq.Array(&i.MediaType),
			&i.Settings,
			&i.Enabled,
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
