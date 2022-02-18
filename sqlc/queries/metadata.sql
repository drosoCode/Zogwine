-- name: GetTag :one
SELECT * FROM tag WHERE id = $1 LIMIT 1;

-- name: ListTagCatg :many
SELECT DISTINCT name FROM tag;

-- name: ListTagByCatg :many
SELECT * FROM tag WHERE name = $1 LIMIT 1;

-- name: ListTagByMedia :many
SELECT * FROM tag t INNER JOIN tag_link l ON (t.id = l.id_tag) WHERE l.media_type = $1 AND l.media_data = $2;

-- name: GetTagByValue :one
SELECT * FROM tag WHERE name = $1 AND value = $2 LIMIT 1;

-- name: AddTag :one
INSERT INTO tag (name, value, icon) VALUES ($1, $2, $3) RETURNING id;

-- name: AddTagLink :exec
INSERT INTO tag_link (id_tag, media_type, media_data) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING;

-- name: DeleteTagLink :exec
DELETE FROM tag_link WHERE id_tag = $1 AND media_type = $2 AND media_data = $3;




-- name: GetPerson :one
SELECT * FROM person WHERE id = $1;

-- name: ListPersonByName :many
SELECT * FROM person WHERE name LIKE $1;

-- name: ListPersonByMedia :many
SELECT * FROM person p INNER JOIN person_link l ON (p.id = l.id_person) WHERE l.media_type = $1 AND l.media_data = $2;

-- name: ListPersonByRole :many
SELECT * FROM person p INNER JOIN person_link l ON (p.id = l.id_person) WHERE l.id_role = $1;

-- name: GetPersonByName :one
SELECT * FROM person WHERE name = $1 LIMIT 1;

-- name: AddPerson :one
INSERT INTO person (name, gender, birth, death, overview, icon, known_for, rating, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15) RETURNING id;

-- name: AddPersonLink :exec
INSERT INTO person_link (id_person, media_type, media_data) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING;

-- name: DeletePersonLink :exec
DELETE FROM person_link WHERE id_person = $1 AND media_type = $2 AND media_data = $3;

-- name: UpdatePerson :exec
UPDATE person t
SET name = CASE WHEN sqlc.arg(name)::TEXT != '' THEN sqlc.arg(name)::TEXT ELSE t.name END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    birth = CASE WHEN sqlc.arg(birth)::BIGINT > 0 THEN sqlc.arg(birth)::BIGINT ELSE t.birth END,
    death = CASE WHEN sqlc.arg(death)::BIGINT > 0 THEN sqlc.arg(death)::BIGINT ELSE t.death END,
    gender = CASE WHEN sqlc.arg(gender)::BIGINT > 0 THEN sqlc.arg(gender)::BIGINT ELSE t.gender END,
    known_for = CASE WHEN sqlc.arg(known_for)::TEXT != '' THEN sqlc.arg(known_for)::TEXT ELSE t.known_for END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT > 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    update_date = $2
WHERE id = $1;





-- name: GetRole :one
SELECT * FROM role WHERE id = $1;

-- name: ListRoleByName :many
SELECT * FROM role WHERE name LIKE $1;

-- name: ListRoleByPerson :many
SELECT * FROM role r INNER JOIN person_link l ON (r.id = l.id_role) WHERE l.id_person = $1;
