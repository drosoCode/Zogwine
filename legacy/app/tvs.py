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


@tvs.route("episode/<int:idEpisode>/status", methods=["PUT"])
def tvs_toggleWatchedEpisodeFlask(idEpisode: int):
    # set episode as watched for user
    tvs_toggleWatchedEpisode(getUID(), idEpisode)
    return jsonify({"status": "ok", "data": "ok"})


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
