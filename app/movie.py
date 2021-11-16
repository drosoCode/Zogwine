from flask import request, Blueprint, jsonify
import redis
import json
from uwsgidecorators import thread
import os.path

from .transcoder import transcoder
from .log import logger
from .utils import checkArgs, checkUser, addCache, encodeImg, getUID, fixTypes
from .scraper import updateWithSelectionResult

from .dbHelper import getSqlConnection, r_runningThreads, configData

# from .indexer import scanner

movie = Blueprint("movie", __name__)

# region COLLECTION

@movie.route("collection", methods=["GET"])
@movie.route("collection/<int:idCollection>", methods=["GET"])
def mov_getCollections(idCollection: int = None):
    idUser = getUID()
    queryData = {"idUser": idUser}
    c = ""
    if idCollection is not None:
        c = "WHERE idCollection = %(idCollection)s "
        queryData.update({"idCollection": idCollection})

    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idCollection AS id, title, overview, "
        "CONCAT('/api/core/image/',icon) AS icon, "
        "CONCAT('/api/core/image/',fanart) AS fanart, "
        "premiered, scraperName, scraperID, scraperLink, addDate, updateDate, "
        "(SELECT COUNT(*) FROM movies m WHERE m.idCollection = t.idCollection) AS movieCount, "
        "(SELECT COUNT(watchCount) FROM movies m LEFT JOIN status st ON (st.idMedia = m.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND m.idCollection = t.idCollection) AS watchedMovies "
        "FROM movie_collections t " + c + "ORDER BY title;",
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
        "rating, premiered, scraperName, scraperID, scraperData, scraperLink, addDate, updateDate, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount "
        "FROM movies t WHERE scraperID IS NOT NULL AND idCollection = %(idCollection)s ORDER BY premiered;",
        {"idUser": idUser, "idCollection": idCollection},
    )
    res = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": fixTypes(res)})


# endregion

# region MOVIE

################################# GET ####################################################


@movie.route("<int:idMovie>", methods=["GET"])
@movie.route("", methods=["GET"])
def mov_getMovieFlask(idMovie: int = None):
    return jsonify({"status": "ok", "data": mov_getMovie(idMovie)})


############################## PUT ####################################


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


@movie.route("<int:idMovie>", methods=["PUT"])
def mov_editMovieData(idMovie: int):
    checkUser("admin")
    allowedFields = [
        "title",
        "overview",
        "icon",
        "fanart",
        "rating",
        "premiered",
        "idCollection",
        "scraperID",
        "scraperName",
        "scraperData",
        "scraperLink",
        "forceUpdate"
    ]
    sqlConnection, cursor = getSqlConnection()
    data = json.loads(request.data)
    err = False
    msg = ""
    setNewScraper = False

    for i, val in data.items():
        if i in allowedFields:
            err, msg = mov_checkPutField(i, val)
            if err:
                break
            else:
                val = msg

            if i not in ["scraperID", "scraperName", "scraperData"]:
                cursor.execute(
                    "UPDATE movies SET " + i + " = %(val)s WHERE idMovie = %(idm)s",
                    {"val": val, "idm": idMovie},
                )
            else:
                setNewScraper = True
        else:
            err = True
            msg = "Unknonw field"
            break

    if not err:
        sqlConnection.commit()

    if setNewScraper:
        cursor.execute("SELECT scraperName, scraperID, scraperData FROM movies WHERE idMovie = %(idMovie)s", {"idMovie": idMovie})
        mov_data = cursor.fetchone()
        scraperName = data.get("scraperName") or mov_data["scraperName"]
        scraperID = data.get("scraperID") or mov_data["scraperID"]
        scraperData = data.get("scraperData") or mov_data["scraperData"]
        updateWithSelectionResult(1, idMovie, scraperName, scraperID, scraperData)

    sqlConnection.close()
    if not err:
        return jsonify({"status": "ok", "data": "ok"})
    else:
        return jsonify({"status": "err", "data": msg}), 400


# endregion

# region HELPERS


def mov_checkPutField(i, val):
    if (i == "icon" or i == "fanart") and val is not None and val[0:4] == "http":
        val = encodeImg(val)

    # check int types
    if i in ["rating", "idLib", "forceUpdate", "idCollection"] and not isinstance(val, int):
        return True, val + " must be of type int"
        
    if i == "forceUpdate" and (int(val) < -1 or int(val) > 1):
        return True, "Invalid value for forceUpdate"

    return False, val

def mov_getMovie(idMovie=None):
    idUser = getUID()
    sqlConnection, cursor = getSqlConnection()
    show = ""
    queryData = {"idUser": int(idUser)}
    if idMovie is not None:
        show = " WHERE idMovie = %(idMovie)s"
        queryData.update({"idMovie": idMovie})

    query = (
        "SELECT idMovie AS id, title, overview, idCollection, "
        "CONCAT('/api/core/image/',icon) AS icon, "
        "CONCAT('/api/core/image/',fanart) AS fanart, "
        "rating, premiered, scraperName, scraperID, scraperData, scraperLink, addDate, updateDate, "
        "(SELECT COALESCE(SUM(watchCount), '0') FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3 AND idMovie = t.idMovie) AS watchCount "
        "FROM movies t " + show + " ORDER BY title;"
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