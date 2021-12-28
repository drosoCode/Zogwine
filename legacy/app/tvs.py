from flask import request, Blueprint, jsonify
import redis
import json
from uwsgidecorators import thread
import os.path
from .log import logger
from .utils import checkUser, addCache, encodeImg, getUID
from .library import checkLibraryType
from .scraper import updateWithSelectionResult

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
        "season, episode, rating, scraperName, scraperID, addDate, updateDate, "
        "(SELECT fillerType FROM fillers WHERE mediaType = 1 AND mediaData = idEpisode) AS filler, "
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

@tvs.route("episode/<int:idEpisode>", methods=["PUT"])
def tvs_editTVSEpisodeData(idEpisode: int):
    checkUser("admin")
    allowedFields = [
        "title",
        "overview",
        "icon",
        "fanart",
        "rating",
        "season",
        "episode",
        "premiered",
        "scraperID",
        "scraperName",
        "scraperData",
        "scraperLink",
        "forceUpdate",
    ]
    sqlConnection, cursor = getSqlConnection()
    data = json.loads(request.data)
    err = False
    msg = ""

    for i, val in data.items():
        if i in allowedFields:
            err, msg = tvs_checkPutField(i, val)
            if err:
                break
            else:
                val = msg

            cursor.execute(
                "UPDATE episodes SET " + i + " = %(val)s WHERE idEpisode = %(idEpisode)s",
                {"val": val, "idEpisode": idEpisode},
            )
        else:
            err = True
            msg = "Unknown field"
            break

    if not err:
        sqlConnection.commit()
    sqlConnection.close()

    if not err:
        return jsonify({"status": "ok", "data": "ok"})
    else:
        return jsonify({"status": "err", "data": msg}), 400


################################# DELETE ####################################################


@tvs.route("episode/<int:idEpisode>", methods=["DELETE"])
def delete_episode(idEpisode: int):
    checkUser("admin")

    sqlConnection, cursor = getSqlConnection()
    idEp = {"id": idEpisode}
    cursor.execute(
        "DELETE FROM status WHERE mediaType = 1 AND idMedia = %(id)s",
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

# region SEASON

# For GET methods, see SHOWS region

########################################################## PUT 

@tvs.route("<int:idShow>/season/<int:season>", methods=["PUT"])
def tvs_editTVSSeasonData(idShow:int, season: int):
    checkUser("admin")
    allowedFields = [
        "title",
        "season",
        "overview",
        "icon",
        "rating",
        "premiered",
        "scraperLink",
        "forceUpdate",
    ]
    sqlConnection, cursor = getSqlConnection()
    data = json.loads(request.data)
    err = False
    msg = ""

    for i, val in data.items():
        if i in allowedFields:
            err, msg = tvs_checkPutField(i, val)
            if err:
                break
            else:
                val = msg

            cursor.execute(
                "UPDATE seasons SET " + i + " = %(val)s WHERE idShow = %(idShow)s AND season = %(season)s",
                {"val": val, "idShow": idShow, "season": season},
            )
        else:
            err = True
            msg = "Unknown field"
            break

    if not err:
        sqlConnection.commit()
    sqlConnection.close()

    if not err:
        return jsonify({"status": "ok", "data": "ok"})
    else:
        return jsonify({"status": "err", "data": msg}), 400

@tvs.route("<int:idShow>/season/<int:season>", methods=["DELETE"])
def tvs_deleteTVSSeason(idShow:int, season: int):
    checkUser("admin")

    sqlConnection, cursor = getSqlConnection()
    idS = {"id": idShow, "season": season}
    cursor.execute(
        "DELETE FROM status WHERE mediaType = 1 AND idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = %(id)s AND season = %(season)s);",
        idS,
    )
    cursor.execute(
        "DELETE FROM video_files WHERE idVid IN (SELECT idVid FROM episodes WHERE idShow = %(id)s AND season = %(season)s);",
        idS,
    )
    cursor.execute("DELETE FROM episodes WHERE idShow = %(id)s AND season = %(season)s", idS)
    cursor.execute("DELETE FROM seasons WHERE idShow = %(id)s AND season = %(season)s", idS)
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
        "SELECT idShow, title, overview, CONCAT('/api/core/image/',icon) AS icon,"
        "season, premiered, scraperLink, addDate, updateDate, "
        "(SELECT COUNT(*) FROM episodes WHERE idShow = s.idShow AND season = s.season) AS episodes, "
        "(SELECT COUNT(watchCount) FROM status WHERE idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = s.idShow AND season = s.season) AND mediaType = 1  AND watchCount > 0 AND idUser = %(idUser)s) AS watchedEpisodes "
        "FROM seasons s "
        "WHERE idShow = %(idShow)s " + s + ""
        "ORDER BY season;",
        dat,
    )
    if season is None:
        res = cursor.fetchall()
    else:
        res = cursor.fetchone()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})



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


# endregion

# region HELPERS


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
        "season, episode, rating, scraperName, scraperID, addDate, updateDate, "
        "(SELECT fillerType FROM fillers WHERE mediaType = 1 AND mediaData = idEpisode) AS filler, "
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

def tvs_checkPutField(i, val):
    if (i == "icon" or i == "fanart") and val is not None and val[0:4] == "http":
        val = encodeImg(val)

    # check int types
    if i in ["rating", "idLib", "forceUpdate"] and not isinstance(val, int):
        return True, val + " must be of type int"

    if i == "idLib":
        if not checkLibraryType(val, 2):
            return True, "Invalid library type"

    if i == "forceUpdate" and (int(val) < -1 or int(val) > 1):
        return True, "Invalid value for forceUpdate"

    return False, val

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
