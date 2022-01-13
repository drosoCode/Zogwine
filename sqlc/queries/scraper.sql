-- name: ListScraperForType :many
SELECT * FROM scraper WHERE media_type @> $1 ORDER BY priority;

