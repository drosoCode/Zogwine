-- Adminer 4.7.8 PostgreSQL dump
-- GRANT ALL PRIVILEGES ON DATABASE "zogwine_dev" to zwtest;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zwtest;

DROP TABLE IF EXISTS "cache";
DROP TABLE IF EXISTS "movie_collection";
DROP TABLE IF EXISTS "movie";
DROP TABLE IF EXISTS "season";
DROP TABLE IF EXISTS "episode";
DROP TABLE IF EXISTS "tv_show";
DROP TABLE IF EXISTS "filler_link";
DROP TABLE IF EXISTS "filler";
DROP TABLE IF EXISTS "upcoming";
DROP TABLE IF EXISTS "video_file";
DROP TABLE IF EXISTS "library";
DROP TABLE IF EXISTS "selection";
DROP TABLE IF EXISTS "scraper";
DROP TABLE IF EXISTS "tag_link";
DROP TABLE IF EXISTS "tag";
DROP TABLE IF EXISTS "person_link";
DROP TABLE IF EXISTS "role";
DROP TABLE IF EXISTS "person";
DROP TABLE IF EXISTS "tracker_link";
DROP TABLE IF EXISTS "tracker";
DROP TABLE IF EXISTS "device";
DROP TABLE IF EXISTS "credential";
DROP TABLE IF EXISTS "status";
DROP TABLE IF EXISTS "group_link";
DROP TABLE IF EXISTS "group";
DROP TABLE IF EXISTS "user";
DROP TYPE IF EXISTS media_type;


CREATE TYPE media_type AS ENUM ('unknonwn', 'tvs_episode', 'tvs', 'movie', 'url', 'tvs_season', 'movie_collection', 'person');


-- ========================= USERS =========================

CREATE TABLE "public"."user" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" text NOT NULL,
    "username" text NOT NULL,
    "password" text NOT NULL,
    "enabled" boolean NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."group" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" text NOT NULL,
    "enabled" boolean NOT NULL,
    "system" boolean NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."group_link" (
    "id_group" BIGINT NOT NULL REFERENCES "group"("id"),
    "id_user" BIGINT NOT NULL REFERENCES "user"("id"),
    PRIMARY KEY ("id_group", "id_user")
) WITH (oids = false);

-- ========================= STATUS =========================

CREATE TABLE "public"."status" (
    "id_user" BIGINT NOT NULL REFERENCES "user"("id"),
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL,
    "watch_count" BIGINT NOT NULL,
    "watch_time" real NOT NULL,
    "last_date" bigint NOT NULL,
    PRIMARY KEY ("id_user", "media_type", "media_data")
) WITH (oids = false);

-- ========================= DEVICES / TRACKERS =========================

CREATE TABLE "public"."credential" (
    "id" BIGSERIAL PRIMARY KEY,
    "username" text NOT NULL,
    "password" text NOT NULL,
    "address" text NOT NULL,
    "port" BIGINT NOT NULL,
    "data" text NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."device" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" text NOT NULL,
    "type" text NOT NULL,
    "id_credential" BIGINT NOT NULL REFERENCES credential("id"),
    "enabled" boolean NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."tracker" (
    "id" BIGSERIAL PRIMARY KEY,
    "id_user" BIGINT NOT NULL REFERENCES "user"("id"),
    "name" text NOT NULL,
    "type" text NOT NULL,
    "id_credential" BIGINT NOT NULL,
    "direction" BIGINT NOT NULL,
    "sync_types" text NOT NULL,
    "enabled" boolean NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."tracker_link" (
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL,
    "id_tracker" BIGINT NOT NULL REFERENCES tracker("id"),
    "tracker_data" text NOT NULL,
    "enabled" boolean NOT NULL,
    PRIMARY KEY ("media_type", "media_data", "id_tracker")
) WITH (oids = false);

-- ========================= PEOPLE / ROLES / TAGS =========================

CREATE TABLE "public"."person" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" text NOT NULL,
    "gender" BIGINT NOT NULL,
    "birth" bigint NOT NULL,
    "death" bigint NOT NULL,
    "overview" text NOT NULL,
    "icon" text NOT NULL,
    "knownFor" text NOT NULL,
    "scraper_name" text NOT NULL,
    "scraper_id" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."role" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" text NOT NULL,
    "overview" text NOT NULL,
    "icon" text NOT NULL,
    "scraper_name" text NOT NULL,
    "scraper_id" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."person_link" (
    "id_person" BIGINT NOT NULL REFERENCES person("id"),
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL,
    "id_role" BIGINT REFERENCES role("id"),
    PRIMARY KEY ("id_person", "media_type", "media_data")
) WITH (oids = false);


CREATE TABLE "public"."tag" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" text NOT NULL,
    "value" text NOT NULL,
    "icon" text NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."tag_link" (
    "id_tag" BIGINT NOT NULL REFERENCES tag("id"),
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL,
    PRIMARY KEY ("media_type", "media_data", "id_tag")
) WITH (oids = false);


-- ========================= SCRAPERS =========================

CREATE TABLE "public"."scraper" (
    "provider" text PRIMARY KEY,
    "priority" BIGINT NOT NULL,
    "media_types" text NOT NULL,
    "settings" json NOT NULL,
    "enabled" boolean NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."selection" (
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL,
    "data" json NOT NULL,
    PRIMARY KEY ("media_type", "media_data")
) WITH (oids = false);

-- ========================= LIBRARIES =========================

CREATE TABLE "public"."library" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" text NOT NULL,
    "path" text NOT NULL,
    "media_type" media_type NOT NULL
) WITH (oids = false);

-- ========================= VIDEO FILES =========================

CREATE TABLE "public"."video_file" (
    "id" BIGSERIAL PRIMARY KEY,
    "id_lib" BIGINT NOT NULL REFERENCES library("id"),
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL,
    "path" text NOT NULL,
    "format" text NOT NULL,
    "duration" real NOT NULL,
    "extension" text NOT NULL,
    "audio" json NOT NULL,
    "subtitle" json NOT NULL,
    "stereo3d" BIGINT NOT NULL,
    "ratio" text NOT NULL,
    "dimension" text NOT NULL,
    "pix_fmt" text NOT NULL,
    "video_codec" text NOT NULL,
    "size" real NOT NULL,
    "tmp" boolean NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL
) WITH (oids = false);

-- ========================= UPCOMING =========================

CREATE TABLE "public"."upcoming" (
    "id" BIGSERIAL PRIMARY KEY,
    "media_type" media_type NOT NULL,
    "ref_media_data" BIGINT NOT NULL,
    "title" text NOT NULL,
    "overview" text NOT NULL,
    "icon" text NOT NULL,
    "date" bigint NOT NULL
) WITH (oids = false);

-- ========================= FILLERS =========================

CREATE TABLE "public"."filler" (
    "id" BIGSERIAL PRIMARY KEY,
    "scraper_name" text NOT NULL,
    "scraper_id" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL,
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."filler_link" (
    "id_filler" BIGINT NOT NULL REFERENCES filler("id"),
    "media_type" media_type NOT NULL,
    "media_data" BIGINT NOT NULL,
    "value" BIGINT NOT NULL,
    PRIMARY KEY ("media_type", "media_data")
) WITH (oids = false);

-- ========================= TV SHOWS =========================

CREATE TABLE "public"."tv_show" (
    "id" BIGSERIAL PRIMARY KEY,
    "title" text NOT NULL,
    "overview" text NOT NULL,
    "icon" text NOT NULL,
    "fanart" text NOT NULL,
    "rating" bigint NOT NULL,
    "premiered" bigint NOT NULL,
    "trailer" text NOT NULL,
    "website" text NOT NULL,
    "scraper_name" text NOT NULL,
    "scraper_id" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "path" text NOT NULL,
    "id_lib" BIGINT NOT NULL REFERENCES library("id"),
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."episode" (
    "id" BIGSERIAL PRIMARY KEY,
    "title" text NOT NULL,
    "overview" text NOT NULL,
    "icon" text NOT NULL,
    "premiered" bigint NOT NULL,
    "season" BIGINT NOT NULL,
    "episode" BIGINT NOT NULL,
    "rating" bigint NOT NULL,
    "scraper_name" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "scraper_id" text NOT NULL,
    "id_show" BIGINT NOT NULL REFERENCES tv_show("id"),
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."season" (
    "id_show" BIGSERIAL NOT NULL REFERENCES tv_show("id"),
    "season" BIGINT NOT NULL,
    "title" text NOT NULL,
    "overview" text NOT NULL,
    "icon" text NOT NULL,
    "fanart" text NOT NULL,
    "premiered" bigint NOT NULL,
    "rating" bigint NOT NULL,
    "scraper_name" text NOT NULL,
    "scraper_id" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL,
    PRIMARY KEY ("id_show", "season")
) WITH (oids = false);

-- ========================= MOVIES =========================

CREATE TABLE "public"."movie" (
    "id" BIGSERIAL PRIMARY KEY,
    "title" text NOT NULL,
    "overview" text NOT NULL,
    "icon" text NOT NULL,
    "fanart" text NOT NULL,
    "premiered" bigint NOT NULL,
    "rating" bigint NOT NULL,
    "trailer" text NOT NULL,
    "website" text NOT NULL,
    "scraper_name" text NOT NULL,
    "scraper_id" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL
) WITH (oids = false);


CREATE TABLE "public"."movie_collection" (
    "id" BIGSERIAL PRIMARY KEY,
    "title" text NOT NULL,
    "overview" text NOT NULL,
    "premiered" bigint NOT NULL,
    "icon" text NOT NULL,
    "fanart" text NOT NULL,
    "rating" bigint NOT NULL,
    "scraper_name" text NOT NULL,
    "scraper_id" text NOT NULL,
    "scraper_data" text NOT NULL,
    "scraper_link" text NOT NULL,
    "add_date" bigint NOT NULL,
    "update_date" bigint NOT NULL,
    "update_mode" BIGINT NOT NULL
) WITH (oids = false);


-- ========================= CACHE ==========================

CREATE TABLE "public"."cache" (
    "id" BIGSERIAL PRIMARY KEY,
    "link" TEXT NOT NULL UNIQUE,
    "extension" TEXT NOT NULL, 
    "cached" BOOLEAN NOT NULL
) WITH (oids = false);

CREATE OR REPLACE FUNCTION FROMCACHE(search_url TEXT)
RETURNS TEXT
LANGUAGE plpgsql
AS
$$
DECLARE
   id_cache integer;
   is_cached boolean;
   ext text;
BEGIN
   IF search_url = '' THEN
       RETURN '';
   END IF;
   SELECT id, extension, cached INTO id_cache, ext, is_cached FROM cache WHERE link = search_url;
    IF FOUND AND is_cached IS true THEN
        RETURN CONCAT('/cache/', id_cache, '.', ext);
    ELSE
        IF SUBSTRING(search_url, 0, 5) = 'http' THEN
            IF NOT FOUND THEN
                INSERT INTO cache (link, extension, cached) VALUES (search_url, '', false);
            END IF;
            RETURN search_url;
        ELSE
            RETURN '';
        END IF;
    END IF;
END;
$$;