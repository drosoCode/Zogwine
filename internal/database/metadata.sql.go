// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.16.0
// source: metadata.sql

package database

import (
	"context"
)

const addPerson = `-- name: AddPerson :one
INSERT INTO person (name, gender, birth, death, overview, icon, known_for, rating, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15) RETURNING id
`

type AddPersonParams struct {
	Name        string `json:"name"`
	Gender      int64  `json:"gender"`
	Birth       int64  `json:"birth"`
	Death       int64  `json:"death"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	KnownFor    string `json:"knownFor"`
	Rating      int64  `json:"rating"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
}

func (q *Queries) AddPerson(ctx context.Context, arg AddPersonParams) (int64, error) {
	row := q.db.QueryRowContext(ctx, addPerson,
		arg.Name,
		arg.Gender,
		arg.Birth,
		arg.Death,
		arg.Overview,
		arg.Icon,
		arg.KnownFor,
		arg.Rating,
		arg.ScraperName,
		arg.ScraperID,
		arg.ScraperData,
		arg.ScraperLink,
		arg.AddDate,
		arg.UpdateDate,
		arg.UpdateMode,
	)
	var id int64
	err := row.Scan(&id)
	return id, err
}

const addPersonLink = `-- name: AddPersonLink :exec
INSERT INTO person_link (id_person, media_type, media_data) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
`

type AddPersonLinkParams struct {
	IDPerson  int64     `json:"idPerson"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) AddPersonLink(ctx context.Context, arg AddPersonLinkParams) error {
	_, err := q.db.ExecContext(ctx, addPersonLink, arg.IDPerson, arg.MediaType, arg.MediaData)
	return err
}

const addTag = `-- name: AddTag :one
INSERT INTO tag (name, value, icon) VALUES ($1, $2, $3) RETURNING id
`

type AddTagParams struct {
	Name  string `json:"name"`
	Value string `json:"value"`
	Icon  string `json:"icon"`
}

func (q *Queries) AddTag(ctx context.Context, arg AddTagParams) (int64, error) {
	row := q.db.QueryRowContext(ctx, addTag, arg.Name, arg.Value, arg.Icon)
	var id int64
	err := row.Scan(&id)
	return id, err
}

const addTagLink = `-- name: AddTagLink :exec
INSERT INTO tag_link (id_tag, media_type, media_data) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
`

type AddTagLinkParams struct {
	IDTag     int64     `json:"idTag"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) AddTagLink(ctx context.Context, arg AddTagLinkParams) error {
	_, err := q.db.ExecContext(ctx, addTagLink, arg.IDTag, arg.MediaType, arg.MediaData)
	return err
}

const deleteAllPersonLinks = `-- name: DeleteAllPersonLinks :exec
DELETE FROM person_link WHERE media_type = $1 AND media_data = $2
`

type DeleteAllPersonLinksParams struct {
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) DeleteAllPersonLinks(ctx context.Context, arg DeleteAllPersonLinksParams) error {
	_, err := q.db.ExecContext(ctx, deleteAllPersonLinks, arg.MediaType, arg.MediaData)
	return err
}

const deleteAllTagLinks = `-- name: DeleteAllTagLinks :exec
DELETE FROM tag_link WHERE media_type = $1 AND media_data = $2
`

type DeleteAllTagLinksParams struct {
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) DeleteAllTagLinks(ctx context.Context, arg DeleteAllTagLinksParams) error {
	_, err := q.db.ExecContext(ctx, deleteAllTagLinks, arg.MediaType, arg.MediaData)
	return err
}

const deletePersonLink = `-- name: DeletePersonLink :exec
DELETE FROM person_link WHERE id_person = $1 AND media_type = $2 AND media_data = $3
`

type DeletePersonLinkParams struct {
	IDPerson  int64     `json:"idPerson"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) DeletePersonLink(ctx context.Context, arg DeletePersonLinkParams) error {
	_, err := q.db.ExecContext(ctx, deletePersonLink, arg.IDPerson, arg.MediaType, arg.MediaData)
	return err
}

const deleteTagLink = `-- name: DeleteTagLink :exec
DELETE FROM tag_link WHERE id_tag = $1 AND media_type = $2 AND media_data = $3
`

type DeleteTagLinkParams struct {
	IDTag     int64     `json:"idTag"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) DeleteTagLink(ctx context.Context, arg DeleteTagLinkParams) error {
	_, err := q.db.ExecContext(ctx, deleteTagLink, arg.IDTag, arg.MediaType, arg.MediaData)
	return err
}

const getPerson = `-- name: GetPerson :one
SELECT id, name, gender, birth, death, overview, icon, known_for, rating, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode FROM person WHERE id = $1
`

func (q *Queries) GetPerson(ctx context.Context, id int64) (Person, error) {
	row := q.db.QueryRowContext(ctx, getPerson, id)
	var i Person
	err := row.Scan(
		&i.ID,
		&i.Name,
		&i.Gender,
		&i.Birth,
		&i.Death,
		&i.Overview,
		&i.Icon,
		&i.KnownFor,
		&i.Rating,
		&i.ScraperName,
		&i.ScraperID,
		&i.ScraperData,
		&i.ScraperLink,
		&i.AddDate,
		&i.UpdateDate,
		&i.UpdateMode,
	)
	return i, err
}

const getPersonByName = `-- name: GetPersonByName :one
SELECT id, name, gender, birth, death, overview, icon, known_for, rating, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode FROM person WHERE name = $1 LIMIT 1
`

func (q *Queries) GetPersonByName(ctx context.Context, name string) (Person, error) {
	row := q.db.QueryRowContext(ctx, getPersonByName, name)
	var i Person
	err := row.Scan(
		&i.ID,
		&i.Name,
		&i.Gender,
		&i.Birth,
		&i.Death,
		&i.Overview,
		&i.Icon,
		&i.KnownFor,
		&i.Rating,
		&i.ScraperName,
		&i.ScraperID,
		&i.ScraperData,
		&i.ScraperLink,
		&i.AddDate,
		&i.UpdateDate,
		&i.UpdateMode,
	)
	return i, err
}

const getRole = `-- name: GetRole :one
SELECT id, name, overview, icon, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode FROM role WHERE id = $1
`

func (q *Queries) GetRole(ctx context.Context, id int64) (Role, error) {
	row := q.db.QueryRowContext(ctx, getRole, id)
	var i Role
	err := row.Scan(
		&i.ID,
		&i.Name,
		&i.Overview,
		&i.Icon,
		&i.ScraperName,
		&i.ScraperID,
		&i.ScraperData,
		&i.ScraperLink,
		&i.AddDate,
		&i.UpdateDate,
		&i.UpdateMode,
	)
	return i, err
}

const getTag = `-- name: GetTag :one
SELECT id, name, value, icon FROM tag WHERE id = $1 LIMIT 1
`

func (q *Queries) GetTag(ctx context.Context, id int64) (Tag, error) {
	row := q.db.QueryRowContext(ctx, getTag, id)
	var i Tag
	err := row.Scan(
		&i.ID,
		&i.Name,
		&i.Value,
		&i.Icon,
	)
	return i, err
}

const getTagByValue = `-- name: GetTagByValue :one
SELECT id, name, value, icon FROM tag WHERE name = $1 AND value = $2 LIMIT 1
`

type GetTagByValueParams struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

func (q *Queries) GetTagByValue(ctx context.Context, arg GetTagByValueParams) (Tag, error) {
	row := q.db.QueryRowContext(ctx, getTagByValue, arg.Name, arg.Value)
	var i Tag
	err := row.Scan(
		&i.ID,
		&i.Name,
		&i.Value,
		&i.Icon,
	)
	return i, err
}

const listPersonByMedia = `-- name: ListPersonByMedia :many
SELECT id, name, gender, birth, death, overview, icon, known_for, rating, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, id_person, media_type, media_data, id_role FROM person p INNER JOIN person_link l ON (p.id = l.id_person) WHERE l.media_type = $1 AND l.media_data = $2
`

type ListPersonByMediaParams struct {
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

type ListPersonByMediaRow struct {
	ID          int64     `json:"id"`
	Name        string    `json:"name"`
	Gender      int64     `json:"gender"`
	Birth       int64     `json:"birth"`
	Death       int64     `json:"death"`
	Overview    string    `json:"overview"`
	Icon        string    `json:"icon"`
	KnownFor    string    `json:"knownFor"`
	Rating      int64     `json:"rating"`
	ScraperName string    `json:"scraperName"`
	ScraperID   string    `json:"scraperID"`
	ScraperData string    `json:"scraperData"`
	ScraperLink string    `json:"scraperLink"`
	AddDate     int64     `json:"addDate"`
	UpdateDate  int64     `json:"updateDate"`
	UpdateMode  int64     `json:"updateMode"`
	IDPerson    int64     `json:"idPerson"`
	MediaType   MediaType `json:"mediaType"`
	MediaData   int64     `json:"mediaData"`
	IDRole      int64     `json:"idRole"`
}

func (q *Queries) ListPersonByMedia(ctx context.Context, arg ListPersonByMediaParams) ([]ListPersonByMediaRow, error) {
	rows, err := q.db.QueryContext(ctx, listPersonByMedia, arg.MediaType, arg.MediaData)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListPersonByMediaRow
	for rows.Next() {
		var i ListPersonByMediaRow
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Gender,
			&i.Birth,
			&i.Death,
			&i.Overview,
			&i.Icon,
			&i.KnownFor,
			&i.Rating,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
			&i.IDPerson,
			&i.MediaType,
			&i.MediaData,
			&i.IDRole,
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

const listPersonByName = `-- name: ListPersonByName :many
SELECT id, name, gender, birth, death, overview, icon, known_for, rating, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode FROM person WHERE name LIKE $1
`

func (q *Queries) ListPersonByName(ctx context.Context, name string) ([]Person, error) {
	rows, err := q.db.QueryContext(ctx, listPersonByName, name)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Person
	for rows.Next() {
		var i Person
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Gender,
			&i.Birth,
			&i.Death,
			&i.Overview,
			&i.Icon,
			&i.KnownFor,
			&i.Rating,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
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

const listPersonByRole = `-- name: ListPersonByRole :many
SELECT id, name, gender, birth, death, overview, icon, known_for, rating, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, id_person, media_type, media_data, id_role FROM person p INNER JOIN person_link l ON (p.id = l.id_person) WHERE l.id_role = $1
`

type ListPersonByRoleRow struct {
	ID          int64     `json:"id"`
	Name        string    `json:"name"`
	Gender      int64     `json:"gender"`
	Birth       int64     `json:"birth"`
	Death       int64     `json:"death"`
	Overview    string    `json:"overview"`
	Icon        string    `json:"icon"`
	KnownFor    string    `json:"knownFor"`
	Rating      int64     `json:"rating"`
	ScraperName string    `json:"scraperName"`
	ScraperID   string    `json:"scraperID"`
	ScraperData string    `json:"scraperData"`
	ScraperLink string    `json:"scraperLink"`
	AddDate     int64     `json:"addDate"`
	UpdateDate  int64     `json:"updateDate"`
	UpdateMode  int64     `json:"updateMode"`
	IDPerson    int64     `json:"idPerson"`
	MediaType   MediaType `json:"mediaType"`
	MediaData   int64     `json:"mediaData"`
	IDRole      int64     `json:"idRole"`
}

func (q *Queries) ListPersonByRole(ctx context.Context, idRole int64) ([]ListPersonByRoleRow, error) {
	rows, err := q.db.QueryContext(ctx, listPersonByRole, idRole)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListPersonByRoleRow
	for rows.Next() {
		var i ListPersonByRoleRow
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Gender,
			&i.Birth,
			&i.Death,
			&i.Overview,
			&i.Icon,
			&i.KnownFor,
			&i.Rating,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
			&i.IDPerson,
			&i.MediaType,
			&i.MediaData,
			&i.IDRole,
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

const listRoleByName = `-- name: ListRoleByName :many
SELECT id, name, overview, icon, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode FROM role WHERE name LIKE $1
`

func (q *Queries) ListRoleByName(ctx context.Context, name string) ([]Role, error) {
	rows, err := q.db.QueryContext(ctx, listRoleByName, name)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Role
	for rows.Next() {
		var i Role
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Overview,
			&i.Icon,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
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

const listRoleByPerson = `-- name: ListRoleByPerson :many
SELECT id, name, overview, icon, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, id_person, media_type, media_data, id_role FROM role r INNER JOIN person_link l ON (r.id = l.id_role) WHERE l.id_person = $1
`

type ListRoleByPersonRow struct {
	ID          int64     `json:"id"`
	Name        string    `json:"name"`
	Overview    string    `json:"overview"`
	Icon        string    `json:"icon"`
	ScraperName string    `json:"scraperName"`
	ScraperID   string    `json:"scraperID"`
	ScraperData string    `json:"scraperData"`
	ScraperLink string    `json:"scraperLink"`
	AddDate     int64     `json:"addDate"`
	UpdateDate  int64     `json:"updateDate"`
	UpdateMode  int64     `json:"updateMode"`
	IDPerson    int64     `json:"idPerson"`
	MediaType   MediaType `json:"mediaType"`
	MediaData   int64     `json:"mediaData"`
	IDRole      int64     `json:"idRole"`
}

func (q *Queries) ListRoleByPerson(ctx context.Context, idPerson int64) ([]ListRoleByPersonRow, error) {
	rows, err := q.db.QueryContext(ctx, listRoleByPerson, idPerson)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListRoleByPersonRow
	for rows.Next() {
		var i ListRoleByPersonRow
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Overview,
			&i.Icon,
			&i.ScraperName,
			&i.ScraperID,
			&i.ScraperData,
			&i.ScraperLink,
			&i.AddDate,
			&i.UpdateDate,
			&i.UpdateMode,
			&i.IDPerson,
			&i.MediaType,
			&i.MediaData,
			&i.IDRole,
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

const listTagByCatg = `-- name: ListTagByCatg :many
SELECT id, name, value, icon FROM tag WHERE name = $1 LIMIT 1
`

func (q *Queries) ListTagByCatg(ctx context.Context, name string) ([]Tag, error) {
	rows, err := q.db.QueryContext(ctx, listTagByCatg, name)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []Tag
	for rows.Next() {
		var i Tag
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Value,
			&i.Icon,
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

const listTagByMedia = `-- name: ListTagByMedia :many
SELECT id, name, value, icon, id_tag, media_type, media_data FROM tag t INNER JOIN tag_link l ON (t.id = l.id_tag) WHERE l.media_type = $1 AND l.media_data = $2
`

type ListTagByMediaParams struct {
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

type ListTagByMediaRow struct {
	ID        int64     `json:"id"`
	Name      string    `json:"name"`
	Value     string    `json:"value"`
	Icon      string    `json:"icon"`
	IDTag     int64     `json:"idTag"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

func (q *Queries) ListTagByMedia(ctx context.Context, arg ListTagByMediaParams) ([]ListTagByMediaRow, error) {
	rows, err := q.db.QueryContext(ctx, listTagByMedia, arg.MediaType, arg.MediaData)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListTagByMediaRow
	for rows.Next() {
		var i ListTagByMediaRow
		if err := rows.Scan(
			&i.ID,
			&i.Name,
			&i.Value,
			&i.Icon,
			&i.IDTag,
			&i.MediaType,
			&i.MediaData,
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

const listTagCatg = `-- name: ListTagCatg :many
SELECT DISTINCT name FROM tag
`

func (q *Queries) ListTagCatg(ctx context.Context) ([]string, error) {
	rows, err := q.db.QueryContext(ctx, listTagCatg)
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

const updatePerson = `-- name: UpdatePerson :exec
UPDATE person t
SET name = CASE WHEN $3::TEXT != '' THEN $3::TEXT ELSE t.name END,
    overview = CASE WHEN $4::TEXT != '' THEN $4::TEXT ELSE t.overview END,
    icon = CASE WHEN $5::TEXT != '' THEN $5::TEXT ELSE t.icon END,
    rating = CASE WHEN $6::BIGINT > 0 THEN $6::BIGINT ELSE t.rating END,
    birth = CASE WHEN $7::BIGINT > 0 THEN $7::BIGINT ELSE t.birth END,
    death = CASE WHEN $8::BIGINT > 0 THEN $8::BIGINT ELSE t.death END,
    gender = CASE WHEN $9::BIGINT > 0 THEN $9::BIGINT ELSE t.gender END,
    known_for = CASE WHEN $10::TEXT != '' THEN $10::TEXT ELSE t.known_for END,
    scraper_id = CASE WHEN $11::TEXT != '' THEN $11::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN $12::TEXT != '' THEN $12::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN $13::TEXT != '' THEN $13::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN $14::TEXT != '' THEN $14::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN $15::BIGINT != 0 THEN $15::BIGINT ELSE t.update_mode END,
    update_date = $2
WHERE id = $1
`

type UpdatePersonParams struct {
	ID          int64  `json:"id"`
	UpdateDate  int64  `json:"updateDate"`
	Name        string `json:"name"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	Rating      int64  `json:"rating"`
	Birth       int64  `json:"birth"`
	Death       int64  `json:"death"`
	Gender      int64  `json:"gender"`
	KnownFor    string `json:"knownFor"`
	ScraperID   string `json:"scraperID"`
	ScraperName string `json:"scraperName"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	UpdateMode  int64  `json:"updateMode"`
}

func (q *Queries) UpdatePerson(ctx context.Context, arg UpdatePersonParams) error {
	_, err := q.db.ExecContext(ctx, updatePerson,
		arg.ID,
		arg.UpdateDate,
		arg.Name,
		arg.Overview,
		arg.Icon,
		arg.Rating,
		arg.Birth,
		arg.Death,
		arg.Gender,
		arg.KnownFor,
		arg.ScraperID,
		arg.ScraperName,
		arg.ScraperData,
		arg.ScraperLink,
		arg.UpdateMode,
	)
	return err
}
