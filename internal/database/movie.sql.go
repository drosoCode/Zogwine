// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.13.0
// source: movie.sql

package database

import (
	"context"
)

const deleteMovie = `-- name: DeleteMovie :exec
DELETE FROM movie WHERE id = $1
`

func (q *Queries) DeleteMovie(ctx context.Context, id int64) error {
	_, err := q.db.ExecContext(ctx, deleteMovie, id)
	return err
}

const deleteMovieCollection = `-- name: DeleteMovieCollection :exec
DELETE FROM movie_collection WHERE id = $1
`

func (q *Queries) DeleteMovieCollection(ctx context.Context, id int64) error {
	_, err := q.db.ExecContext(ctx, deleteMovieCollection, id)
	return err
}

const deleteMovieFile = `-- name: DeleteMovieFile :exec
DELETE FROM video_file WHERE media_type = 'movie' AND media_data = $1
`

func (q *Queries) DeleteMovieFile(ctx context.Context, mediaData int64) error {
	_, err := q.db.ExecContext(ctx, deleteMovieFile, mediaData)
	return err
}

const deleteMovieFileFromCollection = `-- name: DeleteMovieFileFromCollection :exec
DELETE FROM video_file WHERE media_type = 'movie' AND media_data IN (SELECT id FROM movie WHERE id_collection = $1)
`

func (q *Queries) DeleteMovieFileFromCollection(ctx context.Context, idCollection int64) error {
	_, err := q.db.ExecContext(ctx, deleteMovieFileFromCollection, idCollection)
	return err
}

const deleteMovieFromCollection = `-- name: DeleteMovieFromCollection :exec
DELETE FROM movie WHERE id_collection = $1
`

func (q *Queries) DeleteMovieFromCollection(ctx context.Context, idCollection int64) error {
	_, err := q.db.ExecContext(ctx, deleteMovieFromCollection, idCollection)
	return err
}

const deleteMovieStatus = `-- name: DeleteMovieStatus :exec
DELETE FROM status WHERE media_type = 'movie' AND media_data = $1
`

func (q *Queries) DeleteMovieStatus(ctx context.Context, mediaData int64) error {
	_, err := q.db.ExecContext(ctx, deleteMovieStatus, mediaData)
	return err
}

const deleteMovieStatusFromCollection = `-- name: DeleteMovieStatusFromCollection :exec
DELETE FROM status WHERE media_type = 'movie' AND media_data IN (SELECT id FROM movie WHERE id_collection = $1)
`

func (q *Queries) DeleteMovieStatusFromCollection(ctx context.Context, idCollection int64) error {
	_, err := q.db.ExecContext(ctx, deleteMovieStatusFromCollection, idCollection)
	return err
}

const getCollection = `-- name: GetCollection :one
SELECT id, title, overview,
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode,
(SELECT COUNT(*) FROM movie m WHERE m.id_collection = t.id) AS movie_count,
(SELECT COUNT(watch_count) FROM movie m LEFT JOIN status st ON (st.media_data = m.id) WHERE id_user = $1 AND st.media_type = 'movie' AND m.id_collection = t.id) AS watch_count
FROM movie_collection t
WHERE t.id = $2
ORDER BY title
LIMIT 1
`

type GetCollectionParams struct {
	IDUser int64 `json:"idUser"`
	ID     int64 `json:"id"`
}

type GetCollectionRow struct {
	ID          int64  `json:"id"`
	Title       string `json:"title"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	Fanart      string `json:"fanart"`
	Premiered   int64  `json:"premiered"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
	MovieCount  int64  `json:"movieCount"`
	WatchCount  int64  `json:"watchCount"`
}

func (q *Queries) GetCollection(ctx context.Context, arg GetCollectionParams) (GetCollectionRow, error) {
	row := q.db.QueryRowContext(ctx, getCollection, arg.IDUser, arg.ID)
	var i GetCollectionRow
	err := row.Scan(
		&i.ID,
		&i.Title,
		&i.Overview,
		&i.Icon,
		&i.Fanart,
		&i.Premiered,
		&i.ScraperName,
		&i.ScraperID,
		&i.ScraperData,
		&i.ScraperLink,
		&i.AddDate,
		&i.UpdateDate,
		&i.UpdateMode,
		&i.MovieCount,
		&i.WatchCount,
	)
	return i, err
}

const getMovie = `-- name: GetMovie :one
SELECT id, title, overview, id_collection, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, 
COALESCE((SELECT watch_count FROM status st WHERE id_user = $1 AND media_type = 'movie' AND media_data = m.id) ,0) AS watch_count
FROM movie m
WHERE m.id = $2
ORDER BY title
LIMIT 1
`

type GetMovieParams struct {
	IDUser int64 `json:"idUser"`
	ID     int64 `json:"id"`
}

type GetMovieRow struct {
	ID           int64       `json:"id"`
	Title        string      `json:"title"`
	Overview     string      `json:"overview"`
	IDCollection int64       `json:"idCollection"`
	Icon         string      `json:"icon"`
	Fanart       string      `json:"fanart"`
	Trailer      string      `json:"trailer"`
	Rating       int64       `json:"rating"`
	Website      string      `json:"website"`
	Premiered    int64       `json:"premiered"`
	ScraperName  string      `json:"scraperName"`
	ScraperID    string      `json:"scraperID"`
	ScraperData  string      `json:"scraperData"`
	ScraperLink  string      `json:"scraperLink"`
	AddDate      int64       `json:"addDate"`
	UpdateDate   int64       `json:"updateDate"`
	UpdateMode   int64       `json:"updateMode"`
	WatchCount   interface{} `json:"watchCount"`
}

func (q *Queries) GetMovie(ctx context.Context, arg GetMovieParams) (GetMovieRow, error) {
	row := q.db.QueryRowContext(ctx, getMovie, arg.IDUser, arg.ID)
	var i GetMovieRow
	err := row.Scan(
		&i.ID,
		&i.Title,
		&i.Overview,
		&i.IDCollection,
		&i.Icon,
		&i.Fanart,
		&i.Trailer,
		&i.Rating,
		&i.Website,
		&i.Premiered,
		&i.ScraperName,
		&i.ScraperID,
		&i.ScraperData,
		&i.ScraperLink,
		&i.AddDate,
		&i.UpdateDate,
		&i.UpdateMode,
		&i.WatchCount,
	)
	return i, err
}

const listCollection = `-- name: ListCollection :many
SELECT id, title, overview,
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode,
(SELECT COUNT(*) FROM movie m WHERE m.id_collection = t.id) AS movie_count,
(SELECT COUNT(watch_count) FROM movie m LEFT JOIN status st ON (st.media_data = m.id) WHERE id_user = $1 AND st.media_type = 'movie' AND m.id_collection = t.id) AS watch_count
FROM movie_collection t
ORDER BY title
`

type ListCollectionRow struct {
	ID          int64  `json:"id"`
	Title       string `json:"title"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	Fanart      string `json:"fanart"`
	Premiered   int64  `json:"premiered"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
	MovieCount  int64  `json:"movieCount"`
	WatchCount  int64  `json:"watchCount"`
}

func (q *Queries) ListCollection(ctx context.Context, idUser int64) ([]ListCollectionRow, error) {
	rows, err := q.db.QueryContext(ctx, listCollection, idUser)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListCollectionRow
	for rows.Next() {
		var i ListCollectionRow
		if err := rows.Scan(
			&i.ID,
			&i.Title,
			&i.Overview,
			&i.Icon,
			&i.Fanart,
			&i.Premiered,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
			&i.MovieCount,
			&i.WatchCount,
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

const listMovie = `-- name: ListMovie :many
SELECT id, title, overview, id_collection, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, 
COALESCE((SELECT watch_count FROM status st WHERE id_user = $1 AND media_type = 'movie' AND media_data = m.id), 0) AS watch_count
FROM movie m
ORDER BY title
`

type ListMovieRow struct {
	ID           int64       `json:"id"`
	Title        string      `json:"title"`
	Overview     string      `json:"overview"`
	IDCollection int64       `json:"idCollection"`
	Icon         string      `json:"icon"`
	Fanart       string      `json:"fanart"`
	Trailer      string      `json:"trailer"`
	Rating       int64       `json:"rating"`
	Website      string      `json:"website"`
	Premiered    int64       `json:"premiered"`
	ScraperName  string      `json:"scraperName"`
	ScraperID    string      `json:"scraperID"`
	ScraperData  string      `json:"scraperData"`
	ScraperLink  string      `json:"scraperLink"`
	AddDate      int64       `json:"addDate"`
	UpdateDate   int64       `json:"updateDate"`
	UpdateMode   int64       `json:"updateMode"`
	WatchCount   interface{} `json:"watchCount"`
}

func (q *Queries) ListMovie(ctx context.Context, idUser int64) ([]ListMovieRow, error) {
	rows, err := q.db.QueryContext(ctx, listMovie, idUser)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListMovieRow
	for rows.Next() {
		var i ListMovieRow
		if err := rows.Scan(
			&i.ID,
			&i.Title,
			&i.Overview,
			&i.IDCollection,
			&i.Icon,
			&i.Fanart,
			&i.Trailer,
			&i.Rating,
			&i.Website,
			&i.Premiered,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
			&i.WatchCount,
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

const listMovieFromCollection = `-- name: ListMovieFromCollection :many
SELECT id, title, overview, id_collection, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, 
COALESCE((SELECT watch_count FROM status st WHERE id_user = $1 AND media_type = 'movie' AND media_data = m.id), 0) AS watch_count
FROM movie m
WHERE id_collection = $2
ORDER BY title
`

type ListMovieFromCollectionParams struct {
	IDUser       int64 `json:"idUser"`
	IDCollection int64 `json:"idCollection"`
}

type ListMovieFromCollectionRow struct {
	ID           int64       `json:"id"`
	Title        string      `json:"title"`
	Overview     string      `json:"overview"`
	IDCollection int64       `json:"idCollection"`
	Icon         string      `json:"icon"`
	Fanart       string      `json:"fanart"`
	Trailer      string      `json:"trailer"`
	Rating       int64       `json:"rating"`
	Website      string      `json:"website"`
	Premiered    int64       `json:"premiered"`
	ScraperName  string      `json:"scraperName"`
	ScraperID    string      `json:"scraperID"`
	ScraperData  string      `json:"scraperData"`
	ScraperLink  string      `json:"scraperLink"`
	AddDate      int64       `json:"addDate"`
	UpdateDate   int64       `json:"updateDate"`
	UpdateMode   int64       `json:"updateMode"`
	WatchCount   interface{} `json:"watchCount"`
}

func (q *Queries) ListMovieFromCollection(ctx context.Context, arg ListMovieFromCollectionParams) ([]ListMovieFromCollectionRow, error) {
	rows, err := q.db.QueryContext(ctx, listMovieFromCollection, arg.IDUser, arg.IDCollection)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListMovieFromCollectionRow
	for rows.Next() {
		var i ListMovieFromCollectionRow
		if err := rows.Scan(
			&i.ID,
			&i.Title,
			&i.Overview,
			&i.IDCollection,
			&i.Icon,
			&i.Fanart,
			&i.Trailer,
			&i.Rating,
			&i.Website,
			&i.Premiered,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
			&i.WatchCount,
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

const updateMovie = `-- name: UpdateMovie :exec
UPDATE movie t
SET title = CASE WHEN $3::TEXT != '' THEN $3::TEXT ELSE t.title END,
    overview = CASE WHEN $4::TEXT != '' THEN $4::TEXT ELSE t.overview END,
    icon = CASE WHEN $5::TEXT != '' THEN $5::TEXT ELSE t.icon END,
    fanart = CASE WHEN $6::TEXT != '' THEN $6::TEXT ELSE t.fanart END,
    website = CASE WHEN $7::TEXT != '' THEN $7::TEXT ELSE t.website END,
    trailer = CASE WHEN $8::TEXT != '' THEN $8::TEXT ELSE t.trailer END,
    rating = CASE WHEN $9::BIGINT > 0 THEN $9::BIGINT ELSE t.rating END,
    scraper_id = CASE WHEN $10::TEXT != '' THEN $10::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN $11::TEXT != '' THEN $11::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN $12::TEXT != '' THEN $12::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN $13::TEXT != '' THEN $13::TEXT ELSE t.scraper_link END,
    id_collection = CASE WHEN $14::BIGINT > 0 THEN $14::BIGINT ELSE t.id_collection END,
    update_mode = CASE WHEN $15::BIGINT != 0 THEN $15::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN $16::BIGINT > 0 THEN $16::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id = $1
`

type UpdateMovieParams struct {
	ID           int64  `json:"id"`
	UpdateDate   int64  `json:"updateDate"`
	Title        string `json:"title"`
	Overview     string `json:"overview"`
	Icon         string `json:"icon"`
	Fanart       string `json:"fanart"`
	Website      string `json:"website"`
	Trailer      string `json:"trailer"`
	Rating       int64  `json:"rating"`
	ScraperID    string `json:"scraperID"`
	ScraperName  string `json:"scraperName"`
	ScraperData  string `json:"scraperData"`
	ScraperLink  string `json:"scraperLink"`
	IDCollection int64  `json:"idCollection"`
	UpdateMode   int64  `json:"updateMode"`
	Premiered    int64  `json:"premiered"`
}

func (q *Queries) UpdateMovie(ctx context.Context, arg UpdateMovieParams) error {
	_, err := q.db.ExecContext(ctx, updateMovie,
		arg.ID,
		arg.UpdateDate,
		arg.Title,
		arg.Overview,
		arg.Icon,
		arg.Fanart,
		arg.Website,
		arg.Trailer,
		arg.Rating,
		arg.ScraperID,
		arg.ScraperName,
		arg.ScraperData,
		arg.ScraperLink,
		arg.IDCollection,
		arg.UpdateMode,
		arg.Premiered,
	)
	return err
}

const updateMovieCollection = `-- name: UpdateMovieCollection :exec
UPDATE movie t
SET title = CASE WHEN $3::TEXT != '' THEN $3::TEXT ELSE t.title END,
    overview = CASE WHEN $4::TEXT != '' THEN $4::TEXT ELSE t.overview END,
    icon = CASE WHEN $5::TEXT != '' THEN $5::TEXT ELSE t.icon END,
    fanart = CASE WHEN $6::TEXT != '' THEN $6::TEXT ELSE t.fanart END,
    rating = CASE WHEN $7::BIGINT > 0 THEN $7::BIGINT ELSE t.rating END,
    scraper_id = CASE WHEN $8::TEXT != '' THEN $8::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN $9::TEXT != '' THEN $9::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN $10::TEXT != '' THEN $10::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN $11::TEXT != '' THEN $11::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN $12::BIGINT != 0 THEN $12::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN $13::BIGINT > 0 THEN $13::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id = $1
`

type UpdateMovieCollectionParams struct {
	ID          int64  `json:"id"`
	UpdateDate  int64  `json:"updateDate"`
	Title       string `json:"title"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	Fanart      string `json:"fanart"`
	Rating      int64  `json:"rating"`
	ScraperID   string `json:"scraperID"`
	ScraperName string `json:"scraperName"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	UpdateMode  int64  `json:"updateMode"`
	Premiered   int64  `json:"premiered"`
}

func (q *Queries) UpdateMovieCollection(ctx context.Context, arg UpdateMovieCollectionParams) error {
	_, err := q.db.ExecContext(ctx, updateMovieCollection,
		arg.ID,
		arg.UpdateDate,
		arg.Title,
		arg.Overview,
		arg.Icon,
		arg.Fanart,
		arg.Rating,
		arg.ScraperID,
		arg.ScraperName,
		arg.ScraperData,
		arg.ScraperLink,
		arg.UpdateMode,
		arg.Premiered,
	)
	return err
}
