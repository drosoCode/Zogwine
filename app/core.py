from flask import request, Blueprint, jsonify, send_file, redirect
import redis
import json
from uwsgidecorators import thread
from base64 import b64decode
import os

from transcoder import transcoder
from log import logger, getLogs
from utils import checkArgs, checkUser, addCache
from dbHelper import sql
from indexer import scanner

core = Blueprint("core", __name__)
allowedMethods = ["GET", "POST"]
sqlConnectionData = {}
r_userTokens = redis.Redis
r_runningThreads = redis.Redis
configData = {}


def core_configure(conf):
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

    @core.route("/api/core/getStatistics")
    def getStatistics():
        sqlConnection = sql(**sqlConnectionData)
        avgEpTime = 0.5  # h
        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(idStatus) AS watchedEpCount, SUM(watchCount) AS watchedEpSum FROM status WHERE watchCount > 0 AND mediaType = 1 AND idUser = %(idUser)s;",
            {"idUser": r_userTokens.get(request.args["token"])},
        )
        dat1 = cursor.fetchone()
        cursor.execute(
            "SELECT COUNT(DISTINCT idShow) AS tvsCount, COUNT(idEpisode) AS epCount FROM episodes;"
        )
        dat2 = cursor.fetchone()
        cursor.execute(
            "SELECT COUNT(idStatus) AS watchedMovies FROM status WHERE watchCount > 0 AND mediaType = 3 AND idUser = %(idUser)s;",
            {"idUser": r_userTokens.get(request.args["token"])},
        )
        watchedMov = cursor.fetchone()["watchedMovies"]
        cursor.execute("SELECT COUNT(*) AS movCount FROM movies;")
        movCount = cursor.fetchone()["movCount"]
        if "watchedEpSum" not in dat1 or dat1["watchedEpSum"] == None:
            dat1["watchedEpSum"] = 0
        return {
            "watchedEpCount": int(dat1["watchedEpCount"]),
            "watchedEpSum": int(dat1["watchedEpSum"]),
            "tvsCount": int(dat2["tvsCount"]),
            "epCount": int(dat2["epCount"]),
            "moviesCount": int(movCount),
            "watchedMoviesCount": int(watchedMov),
            "lostTime": avgEpTime * int(dat1["watchedEpSum"]),
        }

    @core.route("/api/core/getThreads")
    def getThreadsStatus():
        checkUser(sqlConnectionData, "admin")
        return jsonify(
            {
                "tvs": bool(r_runningThreads.get("tvs") == b"1"),
                "movies": bool(r_runningThreads.get("movies") == b"1"),
                "upEpisodes": bool(r_runningThreads.get("upEpisodes") == b"1"),
                "cache": bool(r_runningThreads.get("cache") == b"1"),
                "people": bool(r_runningThreads.get("people") == b"1"),
            }
        )

    @core.route("/api/core/getLogs")
    def getServerLogs():
        checkUser(sqlConnectionData, "admin")
        try:
            l = int(request.args["amount"])
        except Exception:
            l = 20
        return jsonify(getLogs(l))

    @core.route("/api/image")
    def getImage():
        id = request.args["id"]
        if "http" in id:
            return redirect(id, code=302)

        url = b64decode(id).decode()
        file = "../out/cache/" + id
        ext = url[url.rfind(".") + 1 :]
        mime = "image/" + ext
        if ext == "jpg":
            mime = "image/jpeg"

        if "/" not in id and os.path.exists(file):
            return send_file(open(file, "rb"), mimetype=mime)
        else:
            return redirect(url, code=302)

    @core.route("/api/core/refreshCache", methods=allowedMethods)
    def refreshCacheThreaded():
        checkUser(sqlConnectionData, "admin")
        refreshCache()
        return jsonify({"response": "ok"})

    @thread
    def refreshCache():
        from tvs import tvs_refreshCache
        from movie import mov_refreshCache

        r_runningThreads.set("cache", 1)
        tvs_refreshCache()
        mov_refreshCache()

        sqlConnection = sql(**sqlConnectionData)
        cursor = sqlConnection.cursor(dictionary=True)
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

    @core.route("/api/core/runPeopleScan", methods=allowedMethods)
    def runPeopleScanThreaded():
        checkUser(sqlConnectionData, "admin")
        runPeopleScan()
        return jsonify({"response": "ok"})

    @thread
    def runPeopleScan():
        r_runningThreads.set("people", 1)
        scanner(
            sql(**sqlConnectionData), "people", configData["api"]
        ).getObject().scan()
        r_runningThreads.set("people", 0)

    @core.route("/api/core/getPeople", methods=allowedMethods)
    def getPeople():
        sqlConnection = sql(**sqlConnectionData)
        checkArgs(["mediaType", "mediaData"])
        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute(
            "SELECT p.idPers, role, name, gender, birthdate, deathdate, description, known_for, CONCAT('/api/image?id=',icon) AS icon "
            "FROM people p, people_link l "
            "WHERE p.idPers = l.idPers"
            " AND mediaType = %(mediaType)s AND idMedia = %(mediaData)s;",
            {
                "mediaType": request.args["mediaType"],
                "mediaData": request.args["mediaData"],
            },
        )
        return jsonify(cursor.fetchall())

    @core.route("/api/core/getTags", methods=allowedMethods)
    def getTags():
        sqlConnection = sql(**sqlConnectionData)
        checkArgs(["mediaType", "mediaData"])
        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute(
            "SELECT t.idTag, name, value, CONCAT('/api/image?id=',icon) AS icon "
            "FROM tags t, tags_link l "
            "WHERE t.idTag = l.idTag"
            " AND mediaType = %(mediaType)s AND idMedia = %(mediaData)s;",
            {
                "mediaType": request.args["mediaType"],
                "mediaData": request.args["mediaData"],
            },
        )
        return jsonify(cursor.fetchall())
