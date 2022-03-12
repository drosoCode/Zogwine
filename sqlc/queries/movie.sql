-- name: ListMovie :many
SELECT id, title, overview, id_collection, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, 
COALESCE((SELECT watch_count FROM status st WHERE id_user = $1 AND media_type = 'movie' AND media_data = m.id), 0) AS watch_count
FROM movie m
ORDER BY title;

-- name: GetMovie :one
SELECT id, title, overview, id_collection, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, 
COALESCE((SELECT watch_count FROM status st WHERE id_user = $1 AND media_type = 'movie' AND media_data = m.id) ,0) AS watch_count
FROM movie m
WHERE m.id = $2
ORDER BY title
LIMIT 1;

-- name: ListCollection :many
SELECT id, title, overview,
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode,
(SELECT COUNT(*) FROM movie m WHERE m.id_collection = t.id) AS movie_count,
(SELECT COUNT(watch_count) FROM movie m LEFT JOIN status st ON (st.media_data = m.id) WHERE id_user = $1 AND st.media_type = 'movie' AND m.id_collection = t.id) AS watch_count
FROM movie_collection t
ORDER BY title;

-- name: GetCollection :one
SELECT id, title, overview,
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode,
(SELECT COUNT(*) FROM movie m WHERE m.id_collection = t.id) AS movie_count,
(SELECT COUNT(watch_count) FROM movie m LEFT JOIN status st ON (st.media_data = m.id) WHERE id_user = $1 AND st.media_type = 'movie' AND m.id_collection = t.id) AS watch_count
FROM movie_collection t
WHERE t.id = $2
ORDER BY title
LIMIT 1;

-- name: ListMovieFromCollection :many
SELECT id, title, overview, id_collection, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, 
COALESCE((SELECT watch_count FROM status st WHERE id_user = $1 AND media_type = 'movie' AND media_data = m.id), 0) AS watch_count
FROM movie m
WHERE id_collection = $2
ORDER BY title;

-- name: UpdateMovie :exec
UPDATE movie t
SET title = CASE WHEN sqlc.arg(title)::TEXT != '' THEN sqlc.arg(title)::TEXT ELSE t.title END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    fanart = CASE WHEN sqlc.arg(fanart)::TEXT != '' THEN sqlc.arg(fanart)::TEXT ELSE t.fanart END,
    website = CASE WHEN sqlc.arg(website)::TEXT != '' THEN sqlc.arg(website)::TEXT ELSE t.website END,
    trailer = CASE WHEN sqlc.arg(trailer)::TEXT != '' THEN sqlc.arg(trailer)::TEXT ELSE t.trailer END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    id_collection = CASE WHEN sqlc.arg(id_collection)::BIGINT > 0 THEN sqlc.arg(id_collection)::BIGINT ELSE t.id_collection END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT != 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN sqlc.arg(premiered)::BIGINT > 0 THEN sqlc.arg(premiered)::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id = $1;

-- name: DeleteMovieStatus :exec
DELETE FROM status WHERE media_type = 'movie' AND media_data = $1;
-- name: DeleteMovieFile :exec
DELETE FROM video_file WHERE media_type = 'movie' AND media_data = $1;
-- name: DeleteMovie :exec
DELETE FROM movie WHERE id = $1;


-- name: UpdateMovieCollection :exec
UPDATE movie t
SET title = CASE WHEN sqlc.arg(title)::TEXT != '' THEN sqlc.arg(title)::TEXT ELSE t.title END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    fanart = CASE WHEN sqlc.arg(fanart)::TEXT != '' THEN sqlc.arg(fanart)::TEXT ELSE t.fanart END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT != 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN sqlc.arg(premiered)::BIGINT > 0 THEN sqlc.arg(premiered)::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id = $1;

-- name: DeleteMovieStatusFromCollection :exec
DELETE FROM status WHERE media_type = 'movie' AND media_data IN (SELECT id FROM movie WHERE id_collection = $1);
-- name: DeleteMovieFileFromCollection :exec
DELETE FROM video_file WHERE media_type = 'movie' AND media_data IN (SELECT id FROM movie WHERE id_collection = $1);
-- name: DeleteMovieFromCollection :exec
DELETE FROM movie WHERE id_collection = $1;
-- name: DeleteMovieCollection :exec
DELETE FROM movie_collection WHERE id = $1;