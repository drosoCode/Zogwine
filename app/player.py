import time
from flask import request, Blueprint, jsonify, abort, Response, send_file
import redis
import os
import json
from uwsgidecorators import thread

from .transcoder import transcoder
from .log import logger
from .utils import checkArgs, getFile
from .files import getMediaPath, getFileInfos
from .device import importDevice
from app.devices.PlayerBase import PlayerBase

from .dbHelper import getSqlConnection, r_userFiles, r_userTokens, configData

player = Blueprint("player", __name__)
allowedMethods = ["GET", "POST"]


@player.route("/api/player/start")
def startPlayer():
    checkArgs(["mediaType", "mediaData"])
    uid = r_userTokens.get(request.args["token"])
    logger.info("Starting transcoder for user " + str(uid))

    obj = transcoder(
        int(request.args["mediaType"]),
        int(request.args["mediaData"]),
        os.path.join(configData["config"]["outDir"], request.args["token"]),
        configData["config"]["encoder"],
        configData["config"]["crf"],
    )
    obj.enableHLS(True, configData["config"]["hlsTime"])
    obj.configure(request.args)

    if "idDevice" in request.args and request.args["idDevice"] != "-1":
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "SELECT * FROM devices WHERE idDevice = %(idDevice)s",
            {"idDevice": request.args["idDevice"]},
        )
        data = cursor.fetchone()
        sqlConnection.close()
        if data["enabled"] == 0:
            return False
        dev = importDevice(data["type"])
        device = dev(
            request.args["token"],
            data["address"],
            data["port"],
            data["user"],
            data["password"],
            data["device"],
        )
        startData = device.playMedia(obj)
        if hasattr(device, "doWork"):
            doWork(device)
    else:
        startData = obj.start()

    r_userFiles.set(uid, json.dumps(startData))
    return jsonify({"status": "ok", "data": "ok"})


@thread
def doWork(obj: PlayerBase):
    obj.doWork()


@player.route("/api/player/subtitles")
def getSubtitles():
    checkArgs(["mediaType", "mediaData"])
    if "subStream" in request.args or "subFile" in request.args:
        obj = transcoder(int(request.args["mediaType"]), int(request.args["mediaData"]))
        obj.configure(request.args)
        dat = obj.getSubtitles()
        print(dat)
        return Response(dat, mimetype="text/vtt")
    else:
        abort(404)


@player.route("/api/player/m3u8")
def getTranscoderM3U8():
    token = request.args["token"]
    # add time to fileUrl prevent browser caching
    fileUrl = "/api/player/ts?token=" + token + "&time=" + str(time.time()) + "&name="
    dat = ""

    file = os.path.join(
        configData["config"]["outDir"], request.args["token"], "stream.m3u8"
    )
    if os.path.exists(file):
        fileData = open(file, "r").read()
        for i in fileData.split("\n"):
            if ".ts" in i and "stream" in i:
                dat += fileUrl + i + "\n"
            else:
                dat += i + "\n"
        return Response(dat, mimetype="application/x-mpegURL")
    else:
        abort(404)


@player.route("/api/player/ts")
def getTranscoderFile():
    name = request.args["name"]
    token = request.args["token"]
    # send transcoded file
    file = os.path.join(configData["config"]["outDir"], request.args["token"], name)
    if os.path.exists(file):
        if "/" not in name and "/" not in token:
            return send_file(
                open(file, "rb"),
                mimetype="video/MP2T",
                as_attachment=True,
                attachment_filename=file[file.rfind("/") + 1 :],
            )
        else:
            abort(403)
    else:
        abort(404)


@player.route("/api/player/file")
def player_getFile():
    checkArgs(["mediaType", "mediaData"])
    path = getMediaPath(int(request.args["mediaType"]), int(request.args["mediaData"]))
    if os.path.exists(path):
        return getFile(path, "video")
    else:
        abort(404)


@player.route("/api/player/info", methods=allowedMethods)
def player_getFileInfos():
    checkArgs(["mediaType", "mediaData"])
    mediaType = int(request.args["mediaType"])
    mediaData = int(request.args["mediaData"])

    sqlConnection, cursor = getSqlConnection()
    st = 0
    if mediaType == 1 or mediaType == 3:
        cursor.execute(
            "SELECT watchTime FROM status WHERE idUser = %(idUser)s AND mediaType = %(mediaType)s AND idMedia = %(idMedia)s;",
            {
                "idUser": r_userTokens.get(request.args["token"]),
                "mediaType": mediaType,
                "idMedia": mediaData,
            },
        )
        data = cursor.fetchone()
        if data != None and "watchTime" in data:
            st = float(data["watchTime"])
    sqlConnection.close()

    infos = getFileInfos(mediaType, mediaData)
    infos.update({"startFrom": st})
    return jsonify(
        {
            "status": "ok",
            "data": infos,
        }
    )


@player.route("/api/player/stop", methods=allowedMethods)
def player_stop():
    checkArgs(["mediaType", "mediaData", "endTime"])
    token = request.args["token"]
    mediaType = int(request.args["mediaType"])
    mediaData = int(request.args["mediaData"])
    endTime = float(request.args.get("endTime"))
    # set watch time
    player_setWatchTime(token, mediaType, mediaData, endTime)
    # stop transcoder
    logger.info("Stopping transcoder for user " + str(r_userTokens.get(token)))

    uid = r_userTokens.get(token)

    if "idDevice" in request.args and request.args["idDevice"] != "-1":
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "SELECT * FROM devices WHERE idDevice = %(idDevice)s",
            {"idDevice": request.args["idDevice"]},
        )
        data = cursor.fetchone()
        sqlConnection.close()
        if data["enabled"] == 0:
            return False
        dev = importDevice(data["type"])
        device = dev(
            request.args["token"],
            data["address"],
            data["port"],
            data["user"],
            data["password"],
            data["device"],
        )
        device.stop()
    else:
        transcoder.stop(json.loads(r_userFiles.get(uid)))

    r_userFiles.delete(uid)

    return jsonify({"status": "ok", "data": "ok"})


def player_setWatchTime(token: str, mediaType: int, idMedia: int, endTime: float):
    uid = r_userTokens.get(token)
    sqlConnection, cursor = getSqlConnection()

    duration = 1000000000000000000000000
    if mediaType == 1:
        cursor.execute(
            u"SELECT duration FROM video_files v INNER JOIN episodes e ON (e.idVid = v.idVid) WHERE idEpisode = %(mediaData)s;",
            {u"mediaData": idMedia},
        )
        duration = float(cursor.fetchone()["duration"])
    elif mediaType == 3:
        cursor.execute(
            u"SELECT duration FROM video_files v INNER JOIN movies m ON (m.idVid = v.idVid) WHERE idMovie = %(mediaData)s;",
            {"mediaData": idMedia},
        )
        duration = float(cursor.fetchone()["duration"])
    cursor.execute(
        "SELECT idStatus, watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = %(mediaType)s AND idMedia = %(idMedia)s;",
        {"idUser": uid, "mediaType": mediaType, "idMedia": idMedia},
    )
    data = cursor.fetchone()
    viewAdd = 0

    if endTime > duration * float(configData["config"]["watchedThreshold"]):
        viewAdd = 1
        endTime = 0

    if data != None and "watchCount" in data:
        cursor.execute(
            "UPDATE status SET watchCount = %(watchCount)s, watchTime = %(watchTime)s WHERE idStatus = %(idStatus)s;",
            {
                "watchCount": str(data["watchCount"] + viewAdd),
                "watchTime": str(endTime),
                "idStatus": str(data["idStatus"]),
            },
        )
    else:
        cursor.execute(
            "INSERT INTO status (idUser, mediaType, idMedia, watchCount, watchTime) VALUES (%(idUser)s, %(mediaType)s, %(idMedia)s, %(watchCount)s, %(watchTime)s);",
            {
                "idUser": int(uid),
                "mediaType": mediaType,
                "idMedia": str(idMedia),
                "watchCount": str(viewAdd),
                "watchTime": str(endTime),
            },
        )
    sqlConnection.commit()
    sqlConnection.close()
