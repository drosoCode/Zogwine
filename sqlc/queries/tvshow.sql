--  =============================================== TV SHOWS ===============================================

-- name: ListShow :many
SELECT id, title, overview, 
CONCAT('/api/core/image/',icon)::TEXT AS icon, 
CONCAT('/api/core/image/',fanart)::TEXT AS fanart, 
rating, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, id_lib, path,
(SELECT COUNT(*) FROM season WHERE id_show = t.id)::BIGINT AS season,
(SELECT COUNT(*) FROM episode WHERE id_show = t.id)::BIGINT AS episode,
(SELECT COUNT(*) FROM episode e LEFT JOIN status s ON (s.media_data = e.id)
    WHERE e.id = s.media_data AND s.media_type = 'tvs_episode' AND watch_count > 0  AND id_user = $1 and id_show = t.id) AS watched_episode
FROM tv_show t
ORDER BY title;

-- name: GetShow :one
SELECT id, title, overview, 
CONCAT('/api/core/image/',icon)::TEXT AS icon, 
CONCAT('/api/core/image/',fanart)::TEXT AS fanart, 
rating, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, id_lib, path,
(SELECT COUNT(*) FROM season WHERE id_show = t.id)::BIGINT AS season,
(SELECT COUNT(*) FROM episode WHERE id_show = t.id)::BIGINT AS episode,
(SELECT COUNT(*) FROM episode e LEFT JOIN status s ON (s.media_data = e.id)
    WHERE e.id = s.media_data AND s.media_type = 'tvs_episode' AND watch_count > 0  AND id_user = $1 and id_show = t.id) AS watched_episode
FROM tv_show t
WHERE t.id = $2
LIMIT 1;

-- name: UpdateShow :exec
UPDATE tv_show t
SET title = CASE WHEN sqlc.arg(title)::TEXT != '' THEN sqlc.arg(title)::TEXT ELSE t.title END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    fanart = CASE WHEN sqlc.arg(fanart)::TEXT != '' THEN sqlc.arg(fanart)::TEXT ELSE t.fanart END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating::BIGINT END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    path = CASE WHEN sqlc.arg(path)::TEXT != '' THEN sqlc.arg(path)::TEXT ELSE t.path END,
    id_lib = CASE WHEN sqlc.arg(id_lib)::BIGINT > 0 THEN sqlc.arg(id_lib)::BIGINT ELSE t.id_lib END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT > 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN sqlc.arg(premiered)::BIGINT > 0 THEN sqlc.arg(premiered)::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id = $1;

-- name: UpdateShowIDLib :exec
UPDATE video_file SET id_lib = $1 WHERE media_type = 'tvs_episode' AND media_data IN (SELECT e.id FROM episode e WHERE id_show = $2);

-- name: UpdateShowPath :exec
UPDATE video_file SET path = REGEXP_REPLACE(path, CONCAT('^', (SELECT path FROM tv_show t WHERE t.id = $1)), $2) WHERE media_type = 'tvs_episode' AND media_data IN (SELECT e.id FROM episode e WHERE id_show = $1);

-- name: DeleteShowStatus :exec
DELETE FROM status WHERE media_type = 'tvs_episode' AND media_data IN (SELECT id FROM episode WHERE id_show = $1);
-- name: DeleteShowFile :exec
DELETE FROM video_file WHERE media_type = 'tvs_episode' AND media_data IN (SELECT id FROM episode WHERE id_show = $1);
-- name: DeleteShowEpisode :exec
DELETE FROM episode WHERE id_show = $1;
-- name: DeleteShowSeason :exec
DELETE FROM season WHERE id_show = $1;
-- name: DeleteShow :exec
DELETE FROM tv_show WHERE id = $1;

--  =============================================== SEASONS ===============================================

-- name: ListShowSeason :many
SELECT id_show, title, overview, CONCAT('/api/core/image/',icon)::TEXT AS icon, 
season, premiered, scraper_link, add_date, update_date,
(SELECT COUNT(*) FROM episode WHERE id_show = s.id_show AND season = s.season)::BIGINT AS episode,
(SELECT COUNT(watch_count) FROM status WHERE media_data IN (SELECT id FROM episode WHERE id_show = s.id AND season = s.season) AND media_type = 'tvs_episode'  AND watch_count > 0 AND id_user = $1)::BIGINT AS watchedEpisodes
FROM season s
WHERE s.id_show = $2
ORDER BY season;

-- name: GetShowSeason :one
SELECT s.id_show, title, overview, CONCAT('/api/core/image/',icon)::TEXT AS icon, 
s.season, premiered, scraper_link, add_date, update_date,
(SELECT COUNT(*) FROM episode WHERE id_show = s.id_show AND season = s.season) AS episode,
(SELECT COUNT(watch_count) FROM status WHERE media_data IN (SELECT id FROM episode WHERE id_show = s.id AND season = s.season) AND media_type = 'tvs_episode'  AND watch_count > 0 AND id_user = $1)::BIGINT AS watchedEpisodes
FROM season s
WHERE s.id_show = $2 AND s.season = $3
LIMIT 1;

--  =============================================== EPISODES ===============================================

-- name: GetEpisode :one
SELECT e.id, title, overview, id_show, CONCAT('/api/core/image/',icon)::TEXT AS icon, 
season, episode, rating, scraper_name, scraper_id, add_date, update_date,
(SELECT value FROM filler_link WHERE media_type = 'tvs_episode' AND media_data = id) AS filler,
(SELECT watch_count FROM status WHERE media_data = e.id AND media_type = 'tvs_episode' AND id_user = $1)::BIGINT AS watch_count
FROM episode e
WHERE e.id = $2
LIMIT 1;

-- name: ListEpisodeByShow :many
SELECT e.id, title, overview, id_show, CONCAT('/api/core/image/',icon)::TEXT AS icon, 
season, episode, rating, scraper_name, scraper_id, add_date, update_date,
(SELECT value FROM filler_link WHERE media_type = 'tvs_episode' AND media_data = id) AS filler,
(SELECT watch_count FROM status WHERE media_data = e.id AND media_type = 'tvs_episode' AND id_user = $1)::BIGINT AS watch_count
FROM episode e
WHERE id_show = $2
ORDER BY season, episode;

-- name: ListEpisodeBySeason :many
SELECT e.id, title, overview, id_show, CONCAT('/api/core/image/',icon)::TEXT AS icon, 
season, episode, rating, scraper_name, scraper_id, add_date, update_date,
(SELECT value FROM filler_link WHERE media_type = 'tvs_episode' AND media_data = id) AS filler,
(SELECT watch_count FROM status WHERE media_data = e.id AND media_type = 'tvs_episode' AND id_user = $1)::BIGINT AS watch_count
FROM episode e
WHERE id_show = $2 AND season = $3
ORDER BY season, episode;