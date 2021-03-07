from flask import request, Blueprint, jsonify, send_file, redirect
import redis
import json
from uwsgidecorators import thread
from base64 import b64decode
import os

from .transcoder import transcoder
from .log import logger, getLogs
from .utils import checkArgs, checkUser, addCache, getUID
from .dbHelper import getSqlConnection, r_runningThreads, configData
from .indexer import scanner

core = Blueprint("core", __name__)


@core.route("statistic", methods=["GET"])
def getStatistics():
    uid = getUID()
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT COUNT(idStatus) AS watchedEpCount, SUM(watchCount) AS watchedEpSum FROM status WHERE watchCount > 0 AND mediaType = 1 AND idUser = %(idUser)s;",
        {"idUser": uid},
    )
    dat1 = cursor.fetchone()
    cursor.execute(
        "SELECT COUNT(DISTINCT idShow) AS tvsCount, COUNT(idEpisode) AS epCount FROM episodes;"
    )
    dat2 = cursor.fetchone()
    cursor.execute(
        "SELECT COUNT(idStatus) AS watchedMovies FROM status WHERE watchCount > 0 AND mediaType = 3 AND idUser = %(idUser)s;",
        {"idUser": uid},
    )
    watchedMov = cursor.fetchone()["watchedMovies"]
    cursor.execute("SELECT COUNT(*) AS movCount FROM movies;")
    movCount = cursor.fetchone()["movCount"]
    if "watchedEpSum" not in dat1 or dat1["watchedEpSum"] == None:
        dat1["watchedEpSum"] = 0

    cursor.execute(
        "SELECT SUM(duration*watchCount) AS epTime "
        "FROM video_files v, episodes e, status s "
        "WHERE v.mediaType = 1 "
        "AND s.mediaType = 1 "
        "AND v.idVid = e.idVid "
        "AND e.idEpisode = s.idMedia "
        "AND watchCount > 0 "
        "AND s.idUser = %(user)s",
        {"user": uid},
    )
    lostTime = cursor.fetchone()["epTime"] or 0
    cursor.execute(
        "SELECT SUM(duration*watchCount) AS movTime "
        "FROM video_files v, movies m, status s "
        "WHERE v.mediaType = 3 "
        "AND s.mediaType = 3 "
        "AND v.idVid = m.idVid "
        "AND m.idMovie = s.idMedia "
        "AND watchCount > 0 "
        "AND s.idUser = %(user)s",
        {"user": uid},
    )
    lostTime += cursor.fetchone()["movTime"] or 0

    sqlConnection.close()
    return jsonify(
        {
            "status": "ok",
            "data": {
                "watchedEpisodeCount": int(dat1["watchedEpCount"]),
                "watchedEpisodeSum": int(dat1["watchedEpSum"]),
                "tvsCount": int(dat2["tvsCount"]),
                "episodeCount": int(dat2["epCount"]),
                "movieCount": int(movCount),
                "watchedMovieCount": int(watchedMov),
                "lostTime": round(lostTime / 3600),
            },
        }
    )


@core.route("scan/status")
def getThreadsStatus():
    checkUser("admin")
    return jsonify(
        {
            "status": "ok",
            "data": {
                "tvs": bool(r_runningThreads.get("tvs") == b"1"),
                "movie": bool(r_runningThreads.get("movies") == b"1"),
                "upcomingEpisode": bool(r_runningThreads.get("upEpisodes") == b"1"),
                "cache": bool(r_runningThreads.get("cache") == b"1"),
                "person": bool(r_runningThreads.get("people") == b"1"),
            },
        }
    )


@core.route("log", methods=["GET"])
@core.route("log/<int:amount>", methods=["GET"])
def getServerLogs(amount: int):
    checkUser("admin")
    try:
        l = int(amount)
    except Exception:
        l = 20
    return jsonify({"status": "ok", "data": getLogs(l)})


@core.route("image/<id>", methods=["GET"])
def getImage(id: str):
    if "http" in id:
        return redirect(id, code=302)

    url = b64decode(id).decode()
    file = os.path.join(configData["config"]["outDir"], "cache", id)
    ext = url[url.rfind(".") + 1 :]
    mime = "image/" + ext
    if ext == "jpg":
        mime = "image/jpeg"

    if "/" not in id and os.path.exists(file):
        return redirect("/cache/" + id, code=302)
        # return send_file(open(file, "rb"), mimetype=mime)
    else:
        return redirect(url, code=302)


@core.route("scan/cache", methods=["GET"])
def refreshCacheThreaded():
    checkUser("admin")
    refreshCache()
    return jsonify({"status": "ok", "data": "ok"})


@thread
def refreshCache():
    from .tvs import tvs_refreshCache
    from .movie import mov_refreshCache

    r_runningThreads.set("cache", 1)
    tvs_refreshCache()
    mov_refreshCache()

    sqlConnection, cursor = getSqlConnection()
    # refresh tags cache
    cursor.execute("SELECT icon FROM tags;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])
    # refresh people cache
    cursor.execute("SELECT icon FROM people;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])
    r_runningThreads.set("cache", 0)
    sqlConnection.close()


@core.route("scan/person", methods=["GET"])
def runPeopleScanThreaded():
    checkUser("admin")
    runPeopleScan()
    return jsonify({"status": "ok", "data": "ok"})


@thread
def runPeopleScan():
    r_runningThreads.set("people", 1)
    sqlConnection = getSqlConnection(False)
    scanner(sqlConnection, "people", configData["api"]).getObject().scan()
    r_runningThreads.set("people", 0)
    sqlConnection.close()


@core.route("person", methods=["GET"])
def getPeople():
    sqlConnection, cursor = getSqlConnection()
    checkArgs(["mediaType", "mediaData"])
    cursor.execute(
        "SELECT DISTINCT p.idPers AS id, role, name, gender, birthdate, deathdate, description, known_for, CONCAT('/api/core/image/',icon) AS icon "
        "FROM people p, people_link l "
        "WHERE p.idPers = l.idPers"
        " AND mediaType = %(mediaType)s AND idMedia = %(mediaData)s;",
        {
            "mediaType": request.args["mediaType"],
            "mediaData": request.args["mediaData"],
        },
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})


@core.route("tag", methods=["GET"])
def getTags():
    sqlConnection, cursor = getSqlConnection()
    checkArgs(["mediaType", "mediaData"])
    cursor.execute(
        "SELECT t.idTag AS id, name, value, CONCAT('/api/core/image/',icon) AS icon "
        "FROM tags t, tags_link l "
        "WHERE t.idTag = l.idTag"
        " AND mediaType = %(mediaType)s AND idMedia = %(mediaData)s;",
        {
            "mediaType": request.args["mediaType"],
            "mediaData": request.args["mediaData"],
        },
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})
