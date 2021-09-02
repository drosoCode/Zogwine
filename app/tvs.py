from flask import request, Blueprint, jsonify
import redis
import json
from uwsgidecorators import thread
import os.path
from .log import logger
from .utils import checkUser, addCache, getUID

from .dbHelper import getSqlConnection, r_runningThreads

tvs = Blueprint("tvs", __name__)

# region SCAN

################################# GET ####################################################


@tvs.route("scan/upcoming", methods=["GET"])
def tvs_runUpcomingScanThreaded():
    checkUser("admin")
    tvs_runUpcomingScan()
    return jsonify({"status": "ok", "data": "ok"})


@thread
def tvs_runUpcomingScan():
    r_runningThreads.set("upEpisodes", 1)
    sqlConnection = getSqlConnection(False)
    # scanner(sqlConnection, "tvs", configData["api"]).getObject().scanUpcomingEpisodes()
    r_runningThreads.set("upEpisodes", 0)
    sqlConnection.close()


# endregion

# region EPISODE

################################# GET ####################################################
@tvs.route("episode/upcoming", methods=["GET"])
def get_upcoming_episodes():
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT u.idEpisode AS id, u.title AS title, t.title AS showTitle, u.overview AS overview, CONCAT('/api/core/image/',COALESCE(u.icon, t.fanart)) AS icon,"
        "u.season AS season, u.episode AS episode, u.date AS date, u.idShow AS idShow "
        "FROM upcoming_episodes u, tv_shows t "
        "WHERE u.idShow = t.idShow AND u.date >= DATE(SYSDATE())"
        "ORDER BY date;"
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})


@tvs.route("episode/<int:idEpisode>", methods=["GET"])
def get_episode(idEpisode: int):
    idUser = getUID()
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idEpisode AS id, title, overview, idShow, CONCAT('/api/core/image/',icon) AS icon,"
        "season, episode, rating, scraperName, scraperID, filler, "
        "(SELECT watchCount FROM status WHERE idMedia = e.idEpisode AND mediaType = 1 AND idUser = %(idUser)s) AS watchCount "
        "FROM episodes e "
        "WHERE idEpisode = %(idEpisode)s",
        {"idUser": idUser, "idEpisode": idEpisode},
    )
    res = cursor.fetchone()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})


################################# PUT ####################################################


@tvs.route("episode/<int:idEpisode>/status", methods=["PUT"])
def tvs_toggleWatchedEpisodeFlask(idEpisode: int):
    # set episode as watched for user
    tvs_toggleWatchedEpisode(getUID(), idEpisode)
    return jsonify({"status": "ok", "data": "ok"})


################################# DELETE ####################################################


@tvs.route("episode/<int:idEpisode>", methods=["DELETE"])
def delete_episode(idEpisode: int):
    checkUser("admin")

    sqlConnection, cursor = getSqlConnection()
    idEp = {"id": idEpisode}
    cursor.execute(
        "DELETE FROM status WHERE mediaType = 1 AND idMedia = (SELECT idEpisode FROM episodes WHERE idEpisode = %(id)s);",
        idEp,
    )
    cursor.execute(
        "DELETE FROM video_files WHERE idVid = (SELECT idVid FROM episodes WHERE idEpisode = %(id)s);",
        idEp,
    )
    cursor.execute("DELETE FROM episodes WHERE idEpisode = %(id)s;", idEp)
    sqlConnection.commit()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


# endregion

# region SHOW

################################# GET ####################################################
@tvs.route("<int:idShow>/season/<int:season>/episode", methods=["GET"])
@tvs.route("<int:idShow>/episode", methods=["GET"])
def get_show_episodes(idShow: int, season: int = None):
    return jsonify(
        {
            "status": "ok",
            "data": tvs_getEps(
                idShow,
                season,
            ),
        }
    )


@tvs.route("<int:idShow>", methods=["GET"])
def get_show(idShow: int):
    return jsonify({"status": "ok", "data": tvs_getShows(int(idShow))})


@tvs.route("<int:idShow>/season", methods=["GET"])
@tvs.route("<int:idShow>/season/<int:season>", methods=["GET"])
def get_season(idShow: int, season: int = None):
    idUser = getUID()
    sqlConnection, cursor = getSqlConnection()
    s = ""
    dat = {"idUser": idUser, "idShow": idShow}
    if season is not None:
        dat["season"] = season
        s = "AND season = %(season)s "
    cursor.execute(
        "SELECT title, overview, CONCAT('/api/core/image/',icon) AS icon,"
        "season, premiered, "
        "(SELECT COUNT(*) FROM episodes WHERE idShow = s.idShow AND season = s.season) AS episodes, "
        "(SELECT COUNT(watchCount) FROM status WHERE idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = s.idShow AND season = s.season) AND mediaType = 1  AND watchCount > 0 AND idUser = %(idUser)s) AS watchedEpisodes "
        "FROM seasons s "
        "WHERE idShow = %(idShow)s " + s + ""
        "ORDER BY season;",
        dat,
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})


@tvs.route("", methods=["GET"])
def tvs_getShowsFlask():
    return jsonify({"status": "ok", "data": tvs_getShows()})


################################# POST ####################################################


@tvs.route("<int:idShow>/select/<int:id>", methods=["POST"])
def tvs_setID(idShow: int, id: int):
    checkUser("admin")
    # the resultID is the one from the json list of multipleResults entry
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT multipleResults FROM tv_shows WHERE idShow = %(idShow)s;",
        {"idShow": str(idShow)},
    )
    data = json.loads(cursor.fetchone()["multipleResults"])[int(id)]
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
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


################################# PUT ####################################################


@tvs.route("<int:idShow>/status", methods=["PUT"])
@tvs.route("<int:idShow>/season/<int:season>/status", methods=["PUT"])
def tvs_toggleWatchedSeason(idShow: int, season: int = None):
    uid = getUID()
    sqlConnection, cursor = getSqlConnection()
    dat = {"idUser": getUID(), "idShow": idShow}
    watched = True

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

    ids = tvs_getEps(idShow, season)
    for i in ids:
        if season is None or int(season) == int(i["season"]):
            tvs_toggleWatchedEpisode(uid, i["id"], watched)

    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


@tvs.route("<int:idShow>/scanTitle", methods=["PUT"])
def new_search(idShow: int):
    checkUser("admin")
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "UPDATE tv_shows SET multipleResults = %(newTitle)s, forceUpdate = 1 WHERE idShow = %(idShow)s;",
        {"newTitle": json.loads(request.data)["title"], "idShow": idShow},
    )
    sqlConnection.commit()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


################################# DELETE ####################################################


@tvs.route("<int:idShow>", methods=["DELETE"])
def delete_show(idShow: int):
    checkUser("admin")

    sqlConnection, cursor = getSqlConnection()
    idS = {"id": idShow}
    cursor.execute(
        "DELETE FROM status WHERE mediaType = 1 AND idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = %(id)s);",
        idS,
    )
    cursor.execute(
        "DELETE FROM video_files WHERE idVid IN (SELECT idVid FROM episodes WHERE idShow = %(id)s);",
        idS,
    )
    cursor.execute("DELETE FROM episodes WHERE idShow = %(id)s;", idS)
    cursor.execute("DELETE FROM seasons WHERE idShow = %(id)s;", idS)
    cursor.execute("DELETE FROM tv_shows WHERE idShow = %(id)s;", idS)
    sqlConnection.commit()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


# endregion

# region HELPERS
def tvs_getShows(idShow=None):
    idUser = getUID()
    sqlConnection, cursor = getSqlConnection()
    show = ""
    queryData = {"idUser": int(idUser)}
    if idShow is not None:
        show = " AND idShow = %(idShow)s"
        queryData.update({"idShow": idShow})

    query = (
        "SELECT idShow AS id,"
        "title, overview, CONCAT('/api/core/image/',icon) AS icon, CONCAT('/api/core/image/',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, scraperLink, addDate, updateDate, "
        "(SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons,"
        "(SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes,"
        "(SELECT COUNT(*) FROM episodes e LEFT JOIN status s ON (s.idMedia = e.idEpisode)"
        "WHERE e.idEpisode = s.idMedia AND s.mediaType = 1 AND watchCount > 0  AND idUser = %(idUser)s and idShow = t.idShow) AS watchedEpisodes "
        "FROM tv_shows t "
        "WHERE selectedResult = 1" + show + " ORDER BY title;"
    )

    cursor.execute(query, queryData)
    res = cursor.fetchall()
    sqlConnection.close()
    if idShow is not None:
        return res[0]
    return res


def tvs_getEps(idShow, season=None):
    idUser = getUID()
    sqlConnection, cursor = getSqlConnection()
    s = ""
    dat = {"idUser": idUser, "idShow": idShow}
    if season is not None:
        dat.update({"season": season})
        s = "AND season = %(season)s "
    cursor.execute(
        "SELECT idEpisode AS id, title, overview, CONCAT('/api/core/image/',icon) AS icon,"
        "season, episode, rating, scraperName, scraperID, filler, "
        "(SELECT watchCount FROM status WHERE idMedia = e.idEpisode AND mediaType = 1 AND idUser = %(idUser)s) AS watchCount "
        "FROM episodes e "
        "WHERE idShow = %(idShow)s " + s + ""
        "ORDER BY season, episode;",
        dat,
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return res


def tvs_toggleWatchedEpisode(uid, idEpisode, watched=None):
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idEpisode)s;",
        {"idEpisode": str(idEpisode), "idUser": uid},
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
                "idUser": uid,
                "idMedia": str(idEpisode),
            },
        )
    elif watched is not False:
        cursor.execute(
            "INSERT INTO status (idUser, mediaType, idMedia, watchCount) VALUES (%(idUser)s, 1, %(idMedia)s, 1);",
            {"idUser": uid, "idMedia": str(idEpisode)},
        )
    sqlConnection.commit()
    sqlConnection.close()
    return True


def tvs_refreshCache():
    sqlConnection, cursor = getSqlConnection()
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
    sqlConnection.close()


# endregion
