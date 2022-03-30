-- name: ListScraperForType :many
SELECT * FROM scraper WHERE sqlc.arg(media_type)::media_type = ANY(media_type) ORDER BY priority;

-- name: AddMultipleResults :exec
INSERT INTO selection (media_type, media_data, data, name) VALUES ($1, $2, $3, $4);

-- name: DeleteMultipleResultsByMedia :exec
DELETE FROM selection WHERE media_type = $1 AND media_data = $2;

-- name: GetMultipleResultsByMedia :one
SELECT * FROM selection WHERE media_type = $1 AND media_data = $2 LIMIT 1;

-- name: ListMultipleResultsByMediaType :many
SELECT * FROM selection WHERE media_type = $1;

-- name: ListMultipleResults :many
SELECT * FROM selection;