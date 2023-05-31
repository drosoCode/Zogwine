--  =============================================== TV SHOWS ===============================================

-- name: AddShow :one
INSERT INTO tv_show (title, path, add_date, update_date, id_lib, overview, icon, fanart, rating, premiered, trailer, website, scraper_name, scraper_id, scraper_data, scraper_link, update_mode) 
VALUES ($1, $1, $2, $2, $3, '', '', '', 0, 0, '', '', '', '', '', '', 0) RETURNING id;

-- name: ListShow :many
SELECT id, title, overview, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, id_lib, path,
(SELECT COUNT(*) FROM season WHERE id_show = t.id)::BIGINT AS season,
(SELECT COUNT(*) FROM episode WHERE id_show = t.id)::BIGINT AS episode,
(SELECT COUNT(*) FROM episode e LEFT JOIN status s ON (s.media_data = e.id)
    WHERE e.id = s.media_data AND s.media_type = 'tvs_episode' AND watch_count > 0  AND id_user = $1 and id_show = t.id) AS watched_episode
FROM tv_show t
ORDER BY title;

-- name: GetShow :one
SELECT id, title, overview, 
FROMCACHE(icon) AS icon, 
FROMCACHE(fanart) AS fanart, 
FROMCACHE(trailer) AS trailer, 
rating, website, premiered, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode, id_lib, path,
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
    website = CASE WHEN sqlc.arg(website)::TEXT != '' THEN sqlc.arg(website)::TEXT ELSE t.website END,
    trailer = CASE WHEN sqlc.arg(trailer)::TEXT != '' THEN sqlc.arg(trailer)::TEXT ELSE t.trailer END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    path = CASE WHEN sqlc.arg(path)::TEXT != '' THEN sqlc.arg(path)::TEXT ELSE t.path END,
    id_lib = CASE WHEN sqlc.arg(id_lib)::BIGINT > 0 THEN sqlc.arg(id_lib)::BIGINT ELSE t.id_lib END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT != 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
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

-- name: AddShowSeason :exec
INSERT INTO season (id_show, title, season, overview, icon, fanart, premiered, rating, trailer, scraper_name, scraper_id, scraper_data, scraper_link, add_date, update_date, update_mode) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $14, $15);

-- name: ListShowSeason :many
SELECT id_show, title, overview, FROMCACHE(icon) AS icon, 
season, premiered, rating, trailer, scraper_link, add_date, update_date, update_mode, 
(SELECT COUNT(*) FROM episode WHERE id_show = s.id_show AND season = s.season)::BIGINT AS episode,
(SELECT COUNT(watch_count) FROM status WHERE media_data IN (SELECT id FROM episode e WHERE e.id_show = s.id_show AND season = s.season) AND media_type = 'tvs_episode'  AND watch_count > 0 AND id_user = $1)::BIGINT AS watched_episode
FROM season s
WHERE s.id_show = $2
ORDER BY season;

-- name: GetUnknownSeason :one
SELECT (SELECT COUNT(*) FROM episode WHERE id_show = s.id_show AND season = -1)::BIGINT AS episode,
(SELECT COUNT(watch_count) FROM status WHERE media_data IN (SELECT id FROM episode e WHERE e.id_show = s.id_show AND season = -1) AND media_type = 'tvs_episode'  AND watch_count > 0 AND id_user = $1)::BIGINT AS watched_episode
FROM season s
WHERE s.id_show = $2
ORDER BY season;

-- name: GetShowSeason :one
SELECT s.id_show, title, overview, FROMCACHE(icon) AS icon, 
s.season, premiered, rating, trailer, scraper_link, add_date, update_date, update_mode, 
(SELECT COUNT(*) FROM episode WHERE id_show = s.id_show AND season = s.season) AS episode,
(SELECT COUNT(watch_count) FROM status WHERE media_data IN  (SELECT id FROM episode e WHERE e.id_show = s.id_show AND season = s.season) AND media_type = 'tvs_episode'  AND watch_count > 0 AND id_user = $1)::BIGINT AS watched_episode
FROM season s
WHERE s.id_show = $2 AND s.season = $3
LIMIT 1;

-- name: UpdateShowSeason :exec
UPDATE season t
SET title = CASE WHEN sqlc.arg(title)::TEXT != '' THEN sqlc.arg(title)::TEXT ELSE t.title END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    fanart = CASE WHEN sqlc.arg(fanart)::TEXT != '' THEN sqlc.arg(fanart)::TEXT ELSE t.fanart END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    season = CASE WHEN sqlc.arg(season)::BIGINT > 0 THEN sqlc.arg(season)::BIGINT ELSE t.season END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    trailer = CASE WHEN sqlc.arg(trailer)::TEXT != '' THEN sqlc.arg(trailer)::TEXT ELSE t.trailer END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT != 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN sqlc.arg(premiered)::BIGINT > 0 THEN sqlc.arg(premiered)::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id_show = $1 AND season = sqlc.arg(season)::BIGINT;


-- name: UpdateShowAllSeasons :exec
UPDATE season t
SET title = CASE WHEN sqlc.arg(title)::TEXT != '' THEN sqlc.arg(title)::TEXT ELSE t.title END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    fanart = CASE WHEN sqlc.arg(fanart)::TEXT != '' THEN sqlc.arg(fanart)::TEXT ELSE t.fanart END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    trailer = CASE WHEN sqlc.arg(trailer)::TEXT != '' THEN sqlc.arg(trailer)::TEXT ELSE t.trailer END,
    season = CASE WHEN sqlc.arg(season)::BIGINT > 0 THEN sqlc.arg(season)::BIGINT ELSE t.season END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT != 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN sqlc.arg(premiered)::BIGINT > 0 THEN sqlc.arg(premiered)::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id_show = $1;

-- name: DeleteShowStatusBySeason :exec
DELETE FROM status WHERE media_type = 'tvs_episode' AND media_data IN (SELECT id FROM episode WHERE id_show = $1 AND season = $2);
-- name: DeleteShowFileBySeason :exec
DELETE FROM video_file WHERE media_type = 'tvs_episode' AND media_data IN (SELECT id FROM episode WHERE id_show = $1 AND season = $2);
-- name: DeleteShowEpisodeBySeason :exec
DELETE FROM episode WHERE id_show = $1 AND season = $2;
-- name: DeleteShowSeasonByNum :exec
DELETE FROM season WHERE id_show = $1 AND season = $2;

--  =============================================== EPISODES ===============================================

-- name: AddShowEpisode :one
INSERT INTO episode (title, overview, icon, premiered, season, episode, rating, scraper_name, scraper_id, scraper_data, scraper_link, id_show, add_date, update_date, update_mode) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $13, $14) RETURNING id;

-- name: GetShowEpisode :one
SELECT e.id, title, overview, id_show, premiered, FROMCACHE(icon) AS icon, 
season, episode, rating, scraper_name, scraper_id, add_date, update_date, update_mode, 
COALESCE((SELECT value FROM filler_link WHERE media_type = 'tvs_episode' AND media_data = id), 0) AS filler,
COALESCE((SELECT watch_count FROM status WHERE media_data = e.id AND media_type = 'tvs_episode' AND id_user = $1),0)::BIGINT AS watch_count
FROM episode e
WHERE e.id = $2
LIMIT 1;

-- name: ListShowEpisode :many
SELECT e.id, title, overview, id_show, premiered, FROMCACHE(icon) AS icon, 
season, episode, rating, scraper_name, scraper_id, add_date, update_date, update_mode, 
COALESCE((SELECT value FROM filler_link WHERE media_type = 'tvs_episode' AND media_data = id), 0) AS filler,
COALESCE((SELECT watch_count FROM status WHERE media_data = e.id AND media_type = 'tvs_episode' AND id_user = $1),0)::BIGINT AS watch_count
FROM episode e
WHERE id_show = $2
ORDER BY season, episode;

-- name: ListShowEpisodeBySeason :many
SELECT e.id, title, overview, id_show, premiered, FROMCACHE(icon) AS icon, 
season, episode, rating, scraper_name, scraper_id, add_date, update_date, update_mode, 
COALESCE((SELECT value FROM filler_link WHERE media_type = 'tvs_episode' AND media_data = id), 0) AS filler,
COALESCE((SELECT watch_count FROM status WHERE media_data = e.id AND media_type = 'tvs_episode' AND id_user = $1),0)::BIGINT AS watch_count
FROM episode e
WHERE id_show = $2 AND season = $3
ORDER BY season, episode;

-- name: UpdateShowEpisode :exec
UPDATE episode t
SET title = CASE WHEN sqlc.arg(title)::TEXT != '' THEN sqlc.arg(title)::TEXT ELSE t.title END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    season = CASE WHEN sqlc.arg(season)::BIGINT > 0 THEN sqlc.arg(season)::BIGINT ELSE t.season END,
    episode = CASE WHEN sqlc.arg(episode)::BIGINT > 0 THEN sqlc.arg(episode)::BIGINT ELSE t.episode END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT != 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN sqlc.arg(premiered)::BIGINT > 0 THEN sqlc.arg(premiered)::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id = $1;

-- name: UpdateShowAllEpisodes :exec
UPDATE episode t
SET title = CASE WHEN sqlc.arg(title)::TEXT != '' THEN sqlc.arg(title)::TEXT ELSE t.title END,
    overview = CASE WHEN sqlc.arg(overview)::TEXT != '' THEN sqlc.arg(overview)::TEXT ELSE t.overview END,
    icon = CASE WHEN sqlc.arg(icon)::TEXT != '' THEN sqlc.arg(icon)::TEXT ELSE t.icon END,
    rating = CASE WHEN sqlc.arg(rating)::BIGINT > 0 THEN sqlc.arg(rating)::BIGINT ELSE t.rating END,
    season = CASE WHEN sqlc.arg(season)::BIGINT > 0 THEN sqlc.arg(season)::BIGINT ELSE t.season END,
    episode = CASE WHEN sqlc.arg(episode)::BIGINT > 0 THEN sqlc.arg(episode)::BIGINT ELSE t.episode END,
    scraper_id = CASE WHEN sqlc.arg(scraper_id)::TEXT != '' THEN sqlc.arg(scraper_id)::TEXT ELSE t.scraper_id END,
    scraper_name = CASE WHEN sqlc.arg(scraper_name)::TEXT != '' THEN sqlc.arg(scraper_name)::TEXT ELSE t.scraper_name END,
    scraper_data = CASE WHEN sqlc.arg(scraper_data)::TEXT != '' THEN sqlc.arg(scraper_data)::TEXT ELSE t.scraper_data END,
    scraper_link = CASE WHEN sqlc.arg(scraper_link)::TEXT != '' THEN sqlc.arg(scraper_link)::TEXT ELSE t.scraper_link END,
    update_mode = CASE WHEN sqlc.arg(update_mode)::BIGINT != 0 THEN sqlc.arg(update_mode)::BIGINT ELSE t.update_mode END,
    premiered = CASE WHEN sqlc.arg(premiered)::BIGINT > 0 THEN sqlc.arg(premiered)::BIGINT ELSE t.premiered END,
    update_date = $2
WHERE id_show = $1;

-- name: DeleteShowStatusByEpisode :exec
DELETE FROM status WHERE media_type = 'tvs_episode' AND media_data = $1;
-- name: DeleteShowFileByEpisode :exec
DELETE FROM video_file WHERE media_type = 'tvs_episode' AND media_data = $1;
-- name: DeleteShowEpisodeByID :exec
DELETE FROM episode WHERE id = $1;