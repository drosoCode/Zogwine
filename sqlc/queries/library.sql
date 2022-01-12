-- name: ListLibrary :many
SELECT * FROM library;

-- name: ListLibraryWithType :many
SELECT * FROM library WHERE media_type = $1;

-- name: GetLibrary :one
SELECT * FROM library WHERE id = $1;