from typing import OrderedDict
import json
from uwsgidecorators import thread
from flask import request, Blueprint, jsonify

from .log import logger
from .dbHelper import getSqlConnection, r_runningThreads
from app.scrapers.BaseScraper import BaseScraper
from .utils import checkUser

scraper = Blueprint("scraper", __name__)


def __getScraperFromMediaType(mediaType: int) -> BaseScraper:
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT providerName, settings FROM scrapers WHERE mediaTypes LIKE '%%(mediaType)s;%' OR mediaTypes LIKE '%;%(mediaType)s%' ORDER BY priority",
        {"mediaType": mediaType},
    )
    config = OrderedDict()
    for i in cursor.fetchall():
        config[i["providerName"]] = json.loads(i["settings"])
    sqlConnection.close()

    if mediaType == 1 or mediaType == 2:
        from app.scrapers.tvs import tvs

        return tvs(config)


@scraper.route("result/<mediaType>/<mediaData>", methods=["GET"])
def getScraperResultsMedia(mediaType, mediaData):
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT data FROM selections WHERE mediaType = %(mediaType)s AND mediaData = %(mediaData)s",
        {"mediaType": mediaType, "mediaData": mediaData},
    )
    data = cursor.fetchone()["data"]
    sqlConnection.close()
    return jsonify({"status": "ok", "data": json.loads(data)})


@scraper.route("result", methods=["GET"])
@scraper.route("result/<mediaType>", methods=["GET"])
def getScraperResults(mediaType=None):
    sqlConnection, cursor = getSqlConnection()
    if mediaType is not None:
        cursor.execute(
            "SELECT mediaType, mediaData FROM selections WHERE mediaType = %(mediaType)s",
            {"mediaType": mediaType},
        )
    else:
        cursor.execute("SELECT mediaType, mediaData FROM selections")
    data = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": data})


@scraper.route("select/<mediaType>/<mediaData>/<id>", methods=["POST"])
def selectScraperResults(mediaType, mediaData, id):
    """
    select a specific result for one item
    Args:
        mediaType: the corresponding item type in database
        mediaData: the corresponding item id in database
        id: the id of the selected result
    """
    __getScraperFromMediaType(int(mediaType)).selectScraperResult(mediaData, int(id))
    return jsonify({"status": "ok", "data": "ok"})


@scraper.route("scan/<int:mediaType>/<int:idLib>", methods=["POST"])
def tvs_runScanThreaded(mediaType, idLib):
    checkUser("admin")
    runScan(mediaType, idLib, (request.args.get("autoadd") or False))
    return jsonify({"status": "ok", "data": "ok"})


@thread
def runScan(mediaType, idLib, autoAdd=False):
    # r_runningThreads.set("media_" + str(mediaType), 1)
    __getScraperFromMediaType(int(mediaType)).scan(idLib, autoAdd)
    # r_runningThreads.set("media_" + str(mediaType), 0)
