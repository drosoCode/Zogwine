from flask import request, Blueprint, jsonify
import redis
import json
from uwsgidecorators import thread

from transcoder import transcoder
from log import logger
from utils import checkArgs, checkUser, addCache
from dbHelper import sql
from indexer import scanner

movie = Blueprint("movie", __name__)
allowedMethods = ["GET", "POST"]
sqlConnectionData = {}
r_userTokens = redis.Redis
r_runningThreads = redis.Redis
configData = {}


def movie_configure(conf):
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


def mov_getPath(idMovie):
    sqlConnection = sql(**sqlConnectionData)
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT path FROM movies WHERE idMovie = %(idMovie)s;", {"idMovie": idMovie}
    )
    path = configData["config"]["moviesDirectory"] + "/" + cursor.fetchone()["path"]
    logger.debug("Getting movie path for id:" + str(idMovie) + " -> " + path)
    return path


@movie.route("/api/movies/toggleStatus", methods=allowedMethods)
def mov_toggleStatus():
    sqlConnection = sql(**sqlConnectionData)
    checkArgs(["idMovie"])
    idUser = r_userTokens.get(request.args["token"])
    idMovie = request.args["idMovie"]
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = 3 AND idMedia = %(idMovie)s;",
        {"idMovie": idMovie, "idUser": idUser},
    )
    data = cursor.fetchone()
    count = 0
    if data != None and "watchCount" in data:
        # update
        count = int(data["watchCount"])
        if count > 0:
            count = 0
        else:
            count = 1
        cursor.execute(
            "UPDATE status SET watchCount = %(watchCount)s WHERE idUser = %(idUser)s AND mediaType = 3 AND idMedia = %(idMedia)s;",
            {"watchCount": count, "idUser": idUser, "idMedia": idMovie},
        )
    else:
        cursor.execute(
            "INSERT INTO status (idUser, mediaType, idMedia, watchCount) VALUES (%(idUser)s, 3, %(idMedia)s, 1);",
            {"idUser": idUser, "idMedia": idMovie},
        )
    sqlConnection.commit()
    return jsonify({"response": "ok"})


@movie.route("/api/movies/runScan", methods=allowedMethods)
def mov_runScanThreaded():
    checkUser(sqlConnectionData, "admin")
    mov_runScan()
    return jsonify({"response": "ok"})


@thread
def mov_runScan():
    r_runningThreads.set("movies", 1)
    scanner(sql(**sqlConnectionData), "movies", configData["api"]).scanDir(
        configData["config"]["moviesDirectory"]
    )
    r_runningThreads.set("movies", 0)


def mov_getData(token, mr=False):
    sqlConnection = sql(**sqlConnectionData)
    idUser = r_userTokens.get(token)
    cursor = sqlConnection.cursor(dictionary=True)
    mrDat = ""
    if mr:
        mrDat = "NOT "
    cursor.execute(
        "SELECT idMovie AS id, title, overview, idCollection, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, path, multipleResults, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;",
        {"idUser": idUser},
    )
    return cursor.fetchall()


@movie.route("/api/movies/getMovie", methods=allowedMethods)
def mov_getMovie():
    sqlConnection = sql(**sqlConnectionData)
    checkArgs(["idMovie"])
    idUser = r_userTokens.get(request.args["token"])
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT idMovie AS id, title, overview, idCollection, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, path, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t WHERE idMovie = %(idMovie)s;",
        {"idUser": idUser, "idMovie": request.args["idMovie"]},
    )
    return jsonify(cursor.fetchone())


@movie.route("/api/movies/getMovies", methods=allowedMethods)
def mov_getDataFlask():
    return jsonify(mov_getData(request.args["token"]))


@movie.route("/api/movies/getMultipleResults", methods=allowedMethods)
def mov_getDataMr():
    return jsonify(mov_getData(request.args["token"], True))


@movie.route("/api/movies/getCollections", methods=allowedMethods)
def mov_getCollections():
    sqlConnection = sql(**sqlConnectionData)
    idUser = r_userTokens.get(request.args["token"])
    queryData = {"idUser": idUser}
    c = ""
    if "idCollection" in request.args and request.args["idCollection"] != None:
        c = " WHERE idCollection = %(idCollection)s"
        queryData = {"idUser": idUser, "idCollection": request.args["idCollection"]}
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT idCollection AS id, title, overview, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "premiered, scraperName, scraperID, "
        "(SELECT COUNT(*) FROM movies m WHERE m.idCollection = t.idCollection) movieCount, "
        "(SELECT COUNT(watchCount) FROM movies m LEFT JOIN status st ON (st.idMedia = m.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND m.idCollection = t.idCollection) AS watchedMovies, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movie_collections t " + c + ""
        "ORDER BY title;",
        queryData,
    )
    if c != "":
        return jsonify(cursor.fetchone())
    return jsonify(cursor.fetchall())


@movie.route("/api/movies/getCollectionMovies", methods=allowedMethods)
def mov_getCollectionMovies():
    sqlConnection = sql(**sqlConnectionData)
    checkArgs(["idCollection"])
    idUser = r_userTokens.get(request.args["token"])
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT idMovie AS id, title, overview, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, path, multipleResults, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t WHERE multipleResults IS NULL AND idCollection = %(idCollection)s ORDER BY premiered;",
        {"idUser": idUser, "idCollection": request.args["idCollection"]},
    )
    return jsonify(cursor.fetchall())


@movie.route("/api/movies/setID", methods=allowedMethods)
def mov_setID():
    sqlConnection = sql(**sqlConnectionData)
    checkUser(sqlConnectionData, "admin")
    checkArgs(["idMovie", "id"])
    idMovie = request.args["idMovie"]
    resultID = request.args["id"]
    # the resultID is the one from the json list of multipleResults entry
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT multipleResults FROM movies WHERE idMovie = " + str(idMovie) + ";"
    )
    data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
    cursor.execute(
        "UPDATE movies SET scraperName = %(scraperName)s, scraperID = %(scraperID)s, scraperData = %(scraperData)s, forceUpdate = 1, multipleResults = NULL WHERE idMovie = %(idMovie)s;",
        {
            "scraperName": data["scraperName"],
            "scraperID": data["id"],
            "scraperData": data["scraperData"],
            "idMovie": idMovie,
        },
    )
    sqlConnection.commit()
    return jsonify({"result": "ok"})


@movie.route("/api/movies/setNewSearch", methods=allowedMethods)
def mov_setNewSearch():
    sqlConnection = sql(**sqlConnectionData)
    checkUser(sqlConnectionData, "admin")
    checkArgs(["idMovie", "title"])
    idMovie = request.args["idMovie"]
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "UPDATE movies SET multipleResults = %(newTitle)s, forceUpdate = 1 WHERE idMovie = %(idMovie)s;",
        {"newTitle": request.args["title"], "idMovie": idMovie},
    )
    sqlConnection.commit()
    return jsonify({"result": "ok"})


def mov_refreshCache():
    sqlConnection = sql(**sqlConnectionData)
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT icon, fanart FROM movies;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])
        if d["fanart"] != None and "http" not in d["fanart"]:
            addCache(d["fanart"])
    cursor.execute("SELECT icon, fanart FROM movie_collections;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None and "http" not in d["icon"]:
            addCache(d["icon"])
        if d["fanart"] != None and "http" not in d["fanart"]:
            addCache(d["fanart"])
