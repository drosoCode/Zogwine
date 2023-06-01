-- name: GetEpisodeStat :one
SELECT 
    COUNT(*) AS watched_episode,
    SUM(watch_count) AS watched_episode_count,
    (
        SELECT COUNT(*)
        FROM episode
    ) AS episode_count,
    COALESCE((
        SELECT SUM(duration*watch_count) 
        FROM video_file v, episode e, status s 
        WHERE s.media_type = 'tvs_episode'
        AND v.media_type = 'tvs_episode'
        AND v.media_data = e.id
        AND s.media_data = e.id
        AND watch_count > 0 
        AND s.id_user = $1
    ), 0)::BIGINT AS episode_time
FROM status
WHERE watch_count > 0
    AND media_type = 'tvs_episode'
    AND id_user = $1;

-- name: GetTVShowStat :one
SELECT (
        SELECT COUNT(*)
        FROM (
                SELECT COUNT(*) AS cnt
                FROM episode e1
                GROUP BY e1.id_show
                HAVING COUNT(*) = (
                        SELECT COUNT(*)
                        FROM status s
                        WHERE s.id_user = $1
                            AND s.media_type = 'tvs_episode'
                            AND s.watch_count > 0
                            AND s.media_data IN (
                                SELECT e2.id
                                FROM episode e2
                                WHERE e2.id_show = e1.id_show
                            )
                    )
            ) x
    ) AS watched_tvs,
    (
        SELECT COUNT(*)
        FROM tv_show
    ) AS tvs_count;

-- name: GetMovieStat :one
SELECT COUNT(*) AS watched_movie,
    COALESCE(SUM(watch_count),0)::BIGINT AS watched_movie_count,
    (
        SELECT COUNT(*)
        FROM movie
    ) AS movie_count,
    COALESCE((
        SELECT SUM(duration*watch_count) 
        FROM video_file v, movie m, status s 
        WHERE s.media_type = 'movie' 
        AND v.media_type = 'movie' 
        AND v.media_data = m.id
        AND s.media_data = m.id
        AND watch_count > 0 
        AND s.id_user = $1
    ),0)::BIGINT AS movie_time
FROM status
WHERE watch_count > 0
    AND media_type = 'movie'
    AND id_user = $1;

-- name: ListNotCached :many
SELECT * FROM cache WHERE cached = false;

-- name: UpdateCache :exec
UPDATE cache SET extension = $1, cached = true WHERE id = $2;
