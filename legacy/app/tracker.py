from flask import request, Blueprint, jsonify, abort, Response
import os
import json
from importlib import import_module
from uwsgidecorators import thread

from .log import logger
from .utils import checkArgs, getUID, generateToken, checkUser
from .dbHelper import getSqlConnection, r_userFiles, configData
from .trackers.TVSTracker import TVSTracker
from .trackers.MovieTracker import MovieTracker

tracker = Blueprint("trackers", __name__)


def importTracker(tracker: str):
    if os.path.exists("app/trackers/" + tracker + ".py"):
        module = import_module("app.trackers." + tracker)
        return getattr(module, tracker)


def getAllTrackers():
    conn, cursor = getSqlConnection()
    cursor.execute("SELECT * FROM trackers WHERE enabled = 1")
    trackers = []
    for i in cursor.fetchall():
        trackers.append(
            [
                importTracker(i["type"])(
                    i["idTracker"],
                    i["idUser"],
                    i["user"],
                    i["password"],
                    i["address"],
                    i["port"],
                    i["data"],
                ),
                i["syncTypes"].split(";"),
                i["direction"],
            ]
        )
    conn.close()
    return trackers


@tracker.route("scan/all", methods=["GET"])
def runScanAllThreaded():
    checkUser("admin")
    scanAll()
    return jsonify({"status": "ok", "data": "ok"})


@thread
def scanAll():
    for t in getAllTrackers():
        if ("1" in t[1] or "2" in t[1]) and isinstance(t[0], TVSTracker):
            t[0].scanTVS()
        if ("3" in t[1]) and isinstance(t[0], MovieTracker):
            t[0].scanMovie()


@tracker.route("sync/all", methods=["GET"])
def runSyncAllThreaded():
    checkUser("admin")
    syncAll()
    return jsonify({"status": "ok", "data": "ok"})


@thread
def syncAll():
    for t in getAllTrackers():
        if ("1" in t[1] or "2" in t[1]) and isinstance(t[0], TVSTracker):
            t[0].syncTVS(t[2])
        if ("3" in t[1]) and isinstance(t[0], MovieTracker):
            t[0].syncMovie((t[2]))
