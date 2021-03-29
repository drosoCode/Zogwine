from app.dbHelper import getSqlConnection
from app.log import logger
from app.exceptions import InvalidArgument

from fuzzywuzzy import fuzz, process
from mysql.connector import MySQLConnection


def connectKodi(connectionData: dict) -> tuple:
    if (
        connectionData.get("id") is None
        or connectionData.get("user") is None
        or connectionData.get("password") is None
        or connectionData.get("address") is None
        or connectionData.get("data") is None
    ):
        raise InvalidArgument

    return MySQLConnection(
        host=connectionData["address"] + (":" + str(connectionData["port"]))
        if connectionData.get("port") is not None
        else "",
        user=connectionData["user"],
        password=connectionData["password"],
        database=connectionData["data"],
    )


def searchTVS(connectionData: dict):
    kodiConn = connectKodi(connectionData)
    kodiCursor = kodiConn.cursor()
    zwConn, zwCursor = getSqlConnection()

    existingKodiIDs = []
    existingZwIDs = []
    for i in zwCursor.execute(
        "SELECT mediaData, trackerData FROM trackers_link WHERE mediaType = 2 AND idTracker = %(id)s",
        {"id": connectionData["id"]},
    ):
        existingKodiIDs.append(i["trackerData"])
        existingZwIDs.append(i["mediaData"])

    kodiCursor.execute("SELECT idShow, c00 FROM tvshow")
    ids = {}
    titles = []
    for i in kodiCursor.fetchall():
        if i["idShow"] not in existingKodiIDs:
            ids[i["c00"]] = i["idShow"]
            titles.append(i["c00"])

    zwCursor.execute("SELECT idShow, title FROM tv_shows")
    for i in zwCursor.fetchall():
        if i["idShow"] not in existingZwIDs:
            title, percent = process.extractOne(
                i["title"], titles, scorer=fuzz.token_sort_ratio
            )
            if percent > 85:
                zwCursor.execute(
                    "INSERT INTO trackers_link (mediaType, mediaData, idTracker, trackerData, enabled) VALUES (2, %(mediaData)s, %(idTracker)s, %(trackerData)s, 1)",
                    {
                        "mediaData": i["idShow"],
                        "idTracker": connectionData["id"],
                        "trackerData": ids[title],
                    },
                )
                existingZwIDs.append(i["idShow"])
                titles.remove(title)

    zwConn.commit()
    zwConn.close()
    kodiConn.close()


def syncTVS(connectionData: dict):
    pass


def searchMovie(connectionData: dict):
    pass


def syncMovie(connectionData: dict):
    pass
