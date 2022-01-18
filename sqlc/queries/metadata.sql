-- name: GetTag :one
SELECT * FROM tag WHERE id = $1 LIMIT 1;

-- name: ListTagCatg :many
SELECT DISTINCT name FROM tag;

-- name: ListTagByCatg :many
SELECT * FROM tag WHERE name = $1 LIMIT 1;

-- name: ListTagByMedia :many
SELECT * FROM tag t INNER JOIN tag_link l ON (t.id = l.id_tag) WHERE l.media_type = $1 AND l.media_data = $2;

-- name: GetPerson :one
SELECT * FROM person WHERE id = $1;

-- name: ListPersonByName :many
SELECT * FROM person WHERE name LIKE $1;

-- name: ListPersonByMedia :many
SELECT * FROM person p INNER JOIN person_link l ON (p.id = l.id_person) WHERE l.media_type = $1 AND l.media_data = $2;

-- name: ListPersonByRole :many
SELECT * FROM person p INNER JOIN person_link l ON (p.id = l.id_person) WHERE l.id_role = $1;

-- name: GetRole :one
SELECT * FROM role WHERE id = $1;

-- name: ListRoleByName :many
SELECT * FROM role WHERE name LIKE $1;

-- name: ListRoleByPerson :many
SELECT * FROM role r INNER JOIN person_link l ON (r.id = l.id_role) WHERE l.id_person = $1;
