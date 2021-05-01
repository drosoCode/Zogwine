from flask import request, Blueprint, jsonify
import redis
import json
from uwsgidecorators import thread
import os.path

from .transcoder import transcoder
from .log import logger
from .utils import checkArgs, checkUser, addCache, getUID, fixTypes

from .dbHelper import getSqlConnection, r_runningThreads, configData
from .indexer import scanner

movie = Blueprint("movie", __name__)

# region scan

################################# GET ####################################################


@movie.route("scan", methods=["GET"])
def mov_runScanThreaded():
    checkUser("admin")
    mov_runScan()
    return jsonify({"status": "ok", "data": "ok"})


@movie.route("scan/result", methods=["GET"])
def mov_multipleResults():
    checkUser("admin")
    return jsonify({"status": "ok", "data": mov_getMovie(True)})


# endregion

# region MOVIE


################################# GET ####################################################


@movie.route("<int:idMovie>", methods=["GET"])
@movie.route("", methods=["GET"])
def mov_getMovieFlask(idMovie: int = None):
    return jsonify({"status": "ok", "data": mov_getMovie(False, idMovie)})


@movie.route("collection", methods=["GET"])
@movie.route("collection/<int:idCollection>", methods=["GET"])
def mov_getCollections(idCollection: int = None):
    idUser = getUID()
    queryData = {"idUser": idUser}
    c = ""
    if idCollection is not None:
        c = "WHERE idCollection = %(idCollection)s "
        queryData = {"idUser": idUser, "idCollection": idCollection}
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idCollection AS id, title, overview, "
        "CONCAT('/api/core/image/',icon) AS icon, "
        "CONCAT('/api/core/image/',fanart) AS fanart, "
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
    return jsonify({"status": "ok", "data": fixTypes(res)})


@movie.route("fromCollection/<int:idCollection>", methods=["GET"])
def mov_getCollectionMovies(idCollection: int):
    idUser = getUID()
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idMovie AS id, title, overview, "
        "CONCAT('/api/core/image/',icon) AS icon, "
        "CONCAT('/api/core/image/',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, multipleResults, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t WHERE multipleResults IS NULL AND idCollection = %(idCollection)s ORDER BY premiered;",
        {"idUser": idUser, "idCollection": idCollection},
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": fixTypes(res)})


################################ POST ##########################################################


@movie.route("<int:idMovie>/select/<int:id>", methods=["POST"])
def mov_setID(idMovie: int, id: int):
    checkUser("admin")
    # the id is the one from the json list of multipleResults entry
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT multipleResults FROM movies WHERE idMovie = " + str(idMovie) + ";"
    )
    data = json.loads(cursor.fetchone()["multipleResults"])[int(id)]
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


############################## PUT ####################################


@movie.route("<int:idMovie>/scanTitle", methods=["PUT"])
def mov_setNewSearch(idMovie: int):
    checkUser("admin")
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "UPDATE movies SET multipleResults = %(newTitle)s, forceUpdate = 1 WHERE idMovie = %(idMovie)s;",
        {"newTitle": json.loads(request.data)["title"], "idMovie": idMovie},
    )
    sqlConnection.commit()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": "ok"})


@movie.route("<int:idMovie>/status", methods=["PUT"])
def mov_toggleStatus(idMovie: int):
    idUser = getUID()
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


# endregion

# region HELPERS


@thread
def mov_runScan():
    r_runningThreads.set("movies", 1)
    sqlConnection = getSqlConnection(False)
    scanner(sqlConnection, "movies", configData["api"]).scanDir(
        os.path.join(
            configData["config"]["contentPath"], configData["config"]["moviePath"]
        )
    )
    r_runningThreads.set("movies", 0)
    sqlConnection.close()


def mov_getMovie(mr=False, idMovie=None):
    idUser = getUID()
    sqlConnection, cursor = getSqlConnection()
    mrDat = ""
    show = ""
    queryData = {"idUser": int(idUser)}
    if mr:
        mrDat = "NOT "
    if idMovie is not None:
        show = " AND idMovie = %(idMovie)s"
        queryData.update({"idMovie": idMovie})

    query = (
        "SELECT idMovie AS id, title, overview, idCollection, "
        "CONCAT('/api/core/image/',icon) AS icon, "
        "CONCAT('/api/core/image/',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, multipleResults, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount, "
        "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 3),scraperID) AS scraperLink "
        "FROM movies t "
        "WHERE multipleResults IS " + mrDat + "NULL" + show + " ORDER BY title;"
    )

    cursor.execute(query, queryData)
    res = cursor.fetchall()
    sqlConnection.close()
    if idMovie is not None:
        return fixTypes(res[0])
    return fixTypes(res)


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


# endregion