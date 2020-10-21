from flask import request, Blueprint, jsonify
import redis
import json
from uwsgidecorators import thread

from transcoder import transcoder
from log import logger
from utils import checkArgs, checkUser, addCache
from dbHelper import sql
from indexer import scanner


tvs = Blueprint("tvs", __name__)
allowedMethods = ["GET", "POST"]
sqlConnectionData = {}
r_userTokens = redis.Redis
r_runningThreads = redis.Redis
configData = {}


def tvs_configure(conf):
    global allowedMethods, sqlConnectionData, r_userTokens, r_runningThreads, configData
    configData = conf
    sqlConnectionData = {
        "host": configData["db"]["host"],
        "user": configData["db"]["user"],
        "password": configData["db"]["password"],
        "database": configData["db"]["name"],
        "use_unicode": True,
        "charset": "utf8",
    }
    r_userTokens = redis.Redis(
        host=configData["redis"]["host"],
        port=configData["redis"]["port"],
        db=configData["redis"]["usersDB"],
    )
    r_runningThreads = redis.Redis(
        host=configData["redis"]["host"],
        port=configData["redis"]["port"],
        db=configData["redis"]["threadsDB"],
    )


def tvs_getEpPath(idEpisode):
    sqlConnection = sql(**sqlConnectionData)
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT CONCAT(t.path, '/', e.path) AS path FROM tv_shows t INNER JOIN episodes e ON t.idShow = e.idShow WHERE e.idEpisode = %(idEpisode)s;",
        {"idEpisode": idEpisode},
    )
    path = configData["config"]["tvsDirectory"] + "/" + cursor.fetchone()["path"]
    logger.debug("Getting episode path for id:" + str(idEpisode) + " -> " + path)
    return path


def tvs_refreshCache():
    sqlConnection = sql(**sqlConnectionData)
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT icon, fanart FROM tv_shows;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])
        if d["fanart"] != None and "http" not in d["fanart"]:
            addCache(d["fanart"])
    cursor.execute("SELECT icon FROM episodes;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])
    cursor.execute("SELECT icon FROM seasons;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])
    cursor.execute("SELECT icon FROM upcoming_episodes;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])


@tvs.route("/api/tvs/getUpcomingEpisodes", methods=allowedMethods)
def tvs_getUpcomingEpisodes():
    sqlConnection = sql(**sqlConnectionData)
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT u.idEpisode AS id, u.title AS title, t.title AS showTitle, u.overview AS overview, CONCAT('/api/image?id=',COALESCE(u.icon, t.fanart)) AS icon,"
        "u.season AS season, u.episode AS episode, u.date AS date, u.idShow AS idShow "
        "FROM upcoming_episodes u, tv_shows t "
        "WHERE u.idShow = t.idShow AND u.date >= DATE(SYSDATE())"
        "ORDER BY date;"
    )
    return jsonify(cursor.fetchall())


@tvs.route("/api/tvs/runUpcomingScan", methods=allowedMethods)
def tvs_runUpcomingScanThreaded():
    checkUser(sqlConnectionData, "admin")
    tvs_runUpcomingScan()
    return jsonify({"status": "ok"})


@thread
def tvs_runUpcomingScan():
    r_runningThreads.set("upEpisodes", 1)
    scanner(
        sql(**sqlConnectionData), "tvs", configData["api"]
    ).getObject().scanUpcomingEpisodes()
    r_runningThreads.set("upEpisodes", 0)


def tvs_getEps(token, idShow, season=None):
    sqlConnection = sql(**sqlConnectionData)
    idUser = r_userTokens.get(token)
    cursor = sqlConnection.cursor(dictionary=True)
    s = ""
    dat = {"idUser": idUser, "idShow": idShow}
    if season is not None:
        dat["season"] = season
        s = "AND season = %(season)s "
    cursor.execute(
        "SELECT idEpisode AS id, title, overview, CONCAT('/api/image?id=',icon) AS icon,"
        "season, episode, rating, scraperName, scraperID, "
        "(SELECT watchCount FROM status WHERE idMedia = e.idEpisode AND mediaType = 1 AND idUser = %(idUser)s) AS watchCount "
        "FROM episodes e "
        "WHERE idShow = %(idShow)s " + s + ""
        "ORDER BY season, episode;",
        dat,
    )
    return cursor.fetchall()


@tvs.route("/api/tvs/getEpisodes", methods=allowedMethods)
def tvs_getEpsFlask():
    checkArgs(["idShow"])
    return jsonify(
        tvs_getEps(
            request.args["token"],
            request.args["idShow"],
            request.args.get("season"),
        )
    )


@tvs.route("/api/tvs/getSeasons", methods=allowedMethods)
def tvs_getSeasons():
    sqlConnection = sql(**sqlConnectionData)
    checkArgs(["idShow"])
    idUser = r_userTokens.get(request.args["token"])
    cursor = sqlConnection.cursor(dictionary=True)
    season = request.args.get("season")
    s = ""
    dat = {"idUser": idUser, "idShow": request.args["idShow"]}
    if season is not None:
        dat["season"] = season
        s = "AND season = %(season)s "
    cursor.execute(
        "SELECT title, overview, CONCAT('/api/image?id=',icon) AS icon,"
        "season, premiered, "
        "(SELECT COUNT(*) FROM episodes WHERE idShow = s.idShow AND season = s.season) AS episodes, "
        "(SELECT COUNT(watchCount) FROM status WHERE idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = s.idShow AND season = s.season) AND mediaType = 1 AND idUser = %(idUser)s) AS watchedEpisodes "
        "FROM seasons s "
        "WHERE idShow = %(idShow)s " + s + ""
        "ORDER BY season;",
        dat,
    )
    return jsonify(cursor.fetchall())


def tvs_getShows(token, mr=False):
    sqlConnection = sql(**sqlConnectionData)
    idUser = r_userTokens.get(token)
    cursor = sqlConnection.cursor(dictionary=True)
    mrDat = ""
    if mr:
        mrDat = "NOT "
    query = (
        "SELECT idShow AS id, title,"
        "CONCAT('/api/image?id=',icon) AS icon,"
        "rating, premiered, multipleResults,"
        "(SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons,"
        "(SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes,"
        "(SELECT COUNT(*) FROM episodes e LEFT JOIN status s ON (s.idMedia = e.idEpisode) "
        "WHERE e.idEpisode = s.idMedia AND s.mediaType = 1 AND watchCount > 0  AND idUser = %(idUser)s AND idShow = t.idShow) AS watchedEpisodes "
        "FROM tv_shows t "
        "WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;"
    )
    cursor.execute(query, {"idUser": int(idUser)})
    return cursor.fetchall()


@tvs.route("/api/tvs/getShows", methods=allowedMethods)
def tvs_getShowsFlask():
    return jsonify(tvs_getShows(request.args["token"], False))


@tvs.route("/api/tvs/getShowsMultipleResults", methods=allowedMethods)
def tvs_getShowsMr():
    return jsonify(tvs_getShows(request.args["token"], True))


@tvs.route("/api/tvs/getShow", methods=allowedMethods)
def tvs_getShow():
    sqlConnection = sql(**sqlConnectionData)
    checkArgs(["idShow"])
    idUser = r_userTokens.get(request.args["token"])
    cursor = sqlConnection.cursor(dictionary=True)
    query = (
        "SELECT idShow AS id,"
        "title, overview, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, path,"
        "(SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons,"
        "(SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes,"
        "(SELECT COUNT(*) FROM episodes e LEFT JOIN status s ON (s.idMedia = e.idEpisode)"
        "WHERE e.idEpisode = s.idMedia AND s.mediaType = 1 AND watchCount > 0  AND idUser = %(idUser)s and idShow = t.idShow) AS watchedEpisodes,"
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 1),scraperID) AS scraperLink "
        "FROM tv_shows t "
        "WHERE multipleResults IS NULL AND idShow = %(idShow)s ORDER BY title;"
    )
    cursor.execute(
        query, {"idUser": int(idUser), "idShow": str(request.args["idShow"])}
    )
    return jsonify(cursor.fetchone())


@tvs.route("/api/tvs/setID", methods=allowedMethods)
def tvs_setID():
    sqlConnection = sql(**sqlConnectionData)
    checkArgs(["idShow", "id"])
    checkUser(sqlConnectionData, "admin")

    idShow = request.args["idShow"]
    resultID = request.args["id"]
    # the resultID is the one from the json list of multipleResults entry
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT multipleResults FROM tv_shows WHERE idShow = %(idShow)s;",
        {"idShow": str(idShow)},
    )
    data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
    cursor.execute(
        "UPDATE tv_shows SET scraperName = %(scraperName)s, scraperID = %(scraperId)s, scraperData = %(scraperData)s, forceUpdate = 1, multipleResults = NULL WHERE idShow = %(idShow)s;",
        {
            "scraperName": data["scraperName"],
            "scraperId": data["id"],
            "scraperData": data["scraperData"],
            "idShow": idShow,
        },
    )
    sqlConnection.commit()
    return jsonify({"status": "ok"})


def tvs_toggleWatchedEpisode(token, idEpisode, watched=None):
    sqlConnection = sql(**sqlConnectionData)
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idEpisode)s;",
        {"idEpisode": str(idEpisode), "idUser": int(r_userTokens.get(token))},
    )
    data = cursor.fetchone()
    count = 0
    if data != None and "watchCount" in data:
        # update
        count = data["watchCount"]
        if watched is False or count > 0:
            count = 0
        else:
            count = 1
        cursor.execute(
            "UPDATE status SET watchCount = %(watchCount)s WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idMedia)s;",
            {
                "watchCount": str(count),
                "idUser": int(r_userTokens.get(token)),
                "idMedia": str(idEpisode),
            },
        )
    elif watched is not False:
        cursor.execute(
            "INSERT INTO status (idUser, mediaType, idMedia, watchCount) VALUES (%(idUser)s, 1, %(idMedia)s, 1);",
            {"idUser": int(r_userTokens.get(token)), "idMedia": str(idEpisode)},
        )
    sqlConnection.commit()
    return True


@tvs.route("/api/tvs/toggleEpisodeStatus", methods=allowedMethods)
def tvs_toggleWatchedEpisodeFlask():
    checkArgs(["idEpisode"])
    # set episode as watched for user
    tvs_toggleWatchedEpisode(request.args["token"], request.args["idEpisode"])
    return jsonify({"response": "ok"})


@tvs.route("/api/tvs/toggleSeasonStatus", methods=allowedMethods)
def tvs_toggleWatchedSeason():
    sqlConnection = sql(**sqlConnectionData)
    checkArgs(["idShow"])
    token = request.args["token"]
    idShow = request.args["idShow"]
    cursor = sqlConnection.cursor(dictionary=True)
    dat = {"idUser": r_userTokens.get(token), "idShow": idShow}
    watched = True

    season = request.args.get("season")
    if season is not None:
        dat["season"] = season
        s = "AND season = %(season)s"
    cursor.execute(
        "SELECT SUM(watchCount) AS watched FROM status WHERE idUser = %(idUser)s AND mediaType = 1 "
        "AND idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = %(idShow)s "
        + s
        + ");",
        dat,
    )
    isWatched = cursor.fetchone()["watched"]
    if isWatched is not None and int(isWatched) > 0:
        watched = False

    ids = tvs_getEps(token, idShow)
    for i in ids:
        if season is None or int(season) == int(i["season"]):
            tvs_toggleWatchedEpisode(token, i["id"], watched)

    return jsonify({"response": "ok"})


@tvs.route("/api/tvs/setNewSearch", methods=allowedMethods)
def tvs_setNewSearch():
    sqlConnection = sql(**sqlConnectionData)
    checkUser(sqlConnectionData, "admin")
    checkArgs(["idShow", "title"])
    idShow = request.args["idShow"]
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "UPDATE tv_shows SET multipleResults = %(newTitle)s, forceUpdate = 1 WHERE idShow = %(idShow)s;",
        {"newTitle": request.args["title"], "idShow": idShow},
    )
    sqlConnection.commit()
    return jsonify({"result": "ok"})


@tvs.route("/api/tvs/runScan", methods=allowedMethods)
def tvs_runScanThreaded():
    checkUser(sqlConnectionData, "admin")
    tvs_runScan()
    return jsonify({"response": "ok"})


@thread
def tvs_runScan():
    r_runningThreads.set("tvs", 1)
    scanner(sql(**sqlConnectionData), "tvs", configData["api"]).scanDir(
        configData["config"]["tvsDirectory"]
    )
    r_runningThreads.set("tvs", 0)
