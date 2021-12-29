-- name: UpdateMediaStatus :exec
INSERT INTO status (id_user, media_type, media_data, watch_count, watch_time, last_date)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (id_user, media_type, media_data) DO UPDATE SET 
watch_count = CASE WHEN $4 = 0 THEN 0 ELSE status.watch_count + $4 END,
watch_time = $5, last_date = $6;

-- name: GetMediaStatus :one
SELECT watch_count, watch_time, last_date FROM status WHERE id_user = $1 AND media_type = $2 AND media_data = $3;