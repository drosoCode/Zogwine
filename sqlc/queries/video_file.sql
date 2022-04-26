-- name: AddVideoFile :one
INSERT INTO video_file (id_lib, media_type, media_data, "path", "format", duration, extension, video, audio, subtitle, size, hash, tmp, add_date, update_date) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15) RETURNING id;

-- name: UpdateVideoFile :exec
UPDATE video_file t
SET id_lib = CASE WHEN sqlc.arg(id_lib)::TEXT != '' THEN sqlc.arg(id_lib)::TEXT ELSE t.id_lib END,
    media_type = CASE WHEN sqlc.arg(media_type)::media_type != '' THEN sqlc.arg(media_type)::media_type ELSE t.media_type END,
    media_data = CASE WHEN sqlc.arg(media_data)::BIGINT > 0 THEN sqlc.arg(media_data)::BIGINT ELSE t.media_data END,
    path = CASE WHEN sqlc.arg(path)::TEXT != '' THEN sqlc.arg(path)::TEXT ELSE t.path END,
    format = CASE WHEN sqlc.arg(format)::TEXT != '' THEN sqlc.arg(format)::TEXT ELSE t.format END,
    duration = CASE WHEN sqlc.arg(duration)::double precision > 0 THEN sqlc.arg(duration)::double precision ELSE t.duration END,
    extension = CASE WHEN sqlc.arg(extension)::TEXT != '' THEN sqlc.arg(extension)::TEXT ELSE t.extension END,
    video = CASE WHEN sqlc.arg(video)::json != '' THEN sqlc.arg(video)::json ELSE t.video END,
    audio = CASE WHEN sqlc.arg(audio)::json != '' THEN sqlc.arg(audio)::json ELSE t.audio END,
    subtitle = CASE WHEN sqlc.arg(subtitle)::json != '' THEN sqlc.arg(subtitle)::json ELSE t.subtitle END,
    size = CASE WHEN sqlc.arg(size)::double precision > 0 THEN sqlc.arg(size)::double precision ELSE t.size END,
    hash = CASE WHEN sqlc.arg(hash)::TEXT != '' THEN sqlc.arg(hash)::TEXT ELSE t.hash END,
    update_date = $2
WHERE id = $1;

-- name: ListVideoFileFromMedia :many
SELECT * FROM video_file WHERE media_type = $1 AND media_data = $2;

-- name: GetVideoFile :one
SELECT * FROM video_file WHERE id = $1;

-- name: GetVideoFileFromPath :one
SELECT * FROM video_file WHERE id_lib = $1 AND path = $2 LIMIT 1;

-- name: GetVideoFileFromMedia :one
SELECT * FROM video_file WHERE media_type = $1 AND media_data = $2 ORDER BY id OFFSET $3 LIMIT 1;

-- name: CheckVideoHash :one
SELECT COUNT(*) > 0 AS present FROM video_file WHERE hash = $1;