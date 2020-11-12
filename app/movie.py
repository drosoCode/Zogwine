from flask import request, Blueprint, jsonify
import redis
import json
from uwsgidecorators import thread

from .transcoder import transcoder
from .log import logger
from .utils import checkArgs, checkUser, addCache

from .dbHelper import getSqlConnection, r_userTokens, r_runningThreads, configData
from .indexer import scanner

movie = Blueprint("movie", __name__)
allowedMethods = ["GET", "POST"]


@movie.route("/api/movies/toggleStatus", methods=allowedMethods)
def mov_toggleStatus():
    checkArgs(["idMovie"])
    idUser = r_userTokens.get(request.args["token"])
    idMovie = request.args["idMovie"]
    sqlConnection, cursor = getSqlConnection()
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
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


@movie.route("/api/movies/scan", methods=allowedMethods)
def mov_runScanThreaded():
    checkUser(r_userTokens.get(request.args["token"]), "admin")
    mov_runScan()
    return jsonify({"status": "ok", "data": "ok"})


@thread
def mov_runScan():
    r_runningThreads.set("movies", 1)
    sqlConnection = getSqlConnection(False)
    scanner(sqlConnection, "movies", configData["api"]).scanDir(
        configData["config"]["moviesDirectory"]
    )
    r_runningThreads.set("movies", 0)
    sqlConnection.close()


def mov_getData(token, mr=False):
    idUser = r_userTokens.get(token)
    sqlConnection, cursor = getSqlConnection()
    mrDat = ""
    if mr:
        mrDat = "NOT "
    cursor.execute(
        "SELECT idMovie AS id, title, overview, idCollection, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, multipleResults, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;",
        {"idUser": idUser},
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return res


@movie.route("/api/movies/getMovie", methods=allowedMethods)
def mov_getMovie():
    checkArgs(["idMovie"])
    idUser = r_userTokens.get(request.args["token"])
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idMovie AS id, title, overview, idCollection, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t WHERE idMovie = %(idMovie)s;",
        {"idUser": idUser, "idMovie": request.args["idMovie"]},
    )
    res = cursor.fetchone()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})


@movie.route("/api/movies/getMovies", methods=allowedMethods)
def mov_getDataFlask():
    return jsonify({"status": "ok", "data": mov_getData(request.args["token"])})


@movie.route("/api/movies/getMultipleResults", methods=allowedMethods)
def mov_getDataMr():
    return jsonify({"status": "ok", "data": mov_getData(request.args["token"], True)})


@movie.route("/api/movies/getCollections", methods=allowedMethods)
def mov_getCollections():
    idUser = r_userTokens.get(request.args["token"])
    queryData = {"idUser": idUser}
    c = ""
    if "idCollection" in request.args and request.args["idCollection"] != None:
        c = " WHERE idCollection = %(idCollection)s"
        queryData = {"idUser": idUser, "idCollection": request.args["idCollection"]}
    sqlConnection, cursor = getSqlConnection()
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
        res = cursor.fetchone()
    else:
        res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})


@movie.route("/api/movies/getCollectionMovies", methods=allowedMethods)
def mov_getCollectionMovies():
    checkArgs(["idCollection"])
    idUser = r_userTokens.get(request.args["token"])
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idMovie AS id, title, overview, "
        "CONCAT('/api/image?id=',icon) AS icon, "
        "CONCAT('/api/image?id=',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, multipleResults, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t WHERE multipleResults IS NULL AND idCollection = %(idCollection)s ORDER BY premiered;",
        {"idUser": idUser, "idCollection": request.args["idCollection"]},
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": res})


@movie.route("/api/movies/setID", methods=allowedMethods)
def mov_setID():
    checkUser(r_userTokens.get(request.args["token"]), "admin")
    checkArgs(["idMovie", "id"])
    idMovie = request.args["idMovie"]
    resultID = request.args["id"]
    # the resultID is the one from the json list of multipleResults entry
    sqlConnection, cursor = getSqlConnection()
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
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


@movie.route("/api/movies/setNewSearch", methods=allowedMethods)
def mov_setNewSearch():
    checkUser(r_userTokens.get(request.args["token"]), "admin")
    checkArgs(["idMovie", "title"])
    idMovie = request.args["idMovie"]
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "UPDATE movies SET multipleResults = %(newTitle)s, forceUpdate = 1 WHERE idMovie = %(idMovie)s;",
        {"newTitle": request.args["title"], "idMovie": idMovie},
    )
    sqlConnection.commit()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


def mov_refreshCache():
    sqlConnection, cursor = getSqlConnection()
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
    sqlConnection.close()
