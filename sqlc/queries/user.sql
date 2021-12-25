-- name: GetUserLoginFromUsername :one
SELECT id, password FROM "user" WHERE username = $1 AND enabled = true LIMIT 1;

-- name: ListGroupFromUser :many
SELECT g.name AS name FROM "group" g INNER JOIN group_link l ON (g.id = l.id_group) INNER JOIN "user" u ON (u.id = l.id_user) WHERE u.id = $1 AND g.system = $2;