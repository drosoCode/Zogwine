// Code generated by sqlc. DO NOT EDIT.
// source: status.sql

package database

import (
	"context"
)

const getMediaStatus = `-- name: GetMediaStatus :one
SELECT watch_count, watch_time, last_date FROM status WHERE id_user = $1 AND media_type = $2 AND media_data = $3
`

type GetMediaStatusParams struct {
	IDUser    int64     `json:"idUser"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

type GetMediaStatusRow struct {
	WatchCount int64   `json:"watchCount"`
	WatchTime  float32 `json:"watchTime"`
	LastDate   int64   `json:"lastDate"`
}

func (q *Queries) GetMediaStatus(ctx context.Context, arg GetMediaStatusParams) (GetMediaStatusRow, error) {
	row := q.db.QueryRowContext(ctx, getMediaStatus, arg.IDUser, arg.MediaType, arg.MediaData)
	var i GetMediaStatusRow
	err := row.Scan(&i.WatchCount, &i.WatchTime, &i.LastDate)
	return i, err
}

const updateMediaStatus = `-- name: UpdateMediaStatus :exec
INSERT INTO status (id_user, media_type, media_data, watch_count, watch_time, last_date)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (id_user, media_type, media_data) DO UPDATE SET 
watch_count = CASE WHEN $4 = 0 THEN 0 ELSE status.watch_count + $4 END,
watch_time = $5, last_date = $6
`

type UpdateMediaStatusParams struct {
	IDUser     int64     `json:"idUser"`
	MediaType  MediaType `json:"mediaType"`
	MediaData  int64     `json:"mediaData"`
	WatchCount int64     `json:"watchCount"`
	WatchTime  float32   `json:"watchTime"`
	LastDate   int64     `json:"lastDate"`
}

func (q *Queries) UpdateMediaStatus(ctx context.Context, arg UpdateMediaStatusParams) error {
	_, err := q.db.ExecContext(ctx, updateMediaStatus,
		arg.IDUser,
		arg.MediaType,
		arg.MediaData,
		arg.WatchCount,
		arg.WatchTime,
		arg.LastDate,
	)
	return err
}
