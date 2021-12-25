import time
from flask import request, Blueprint, jsonify, abort, Response, send_file, redirect
import redis
import os
import json
from uwsgidecorators import thread

from app.library import checkLibraryType

from .transcoder import transcoder
from .log import logger
from .utils import checkArgs, checkUser, getUID, generateToken
from .files import getIdVid, getMediaPath, getFileInfos
from .device import importDevice
from app.devices.PlayerBase import PlayerBase

from .dbHelper import getSqlConnection, r_userFiles, r_userTokens, configData

player = Blueprint("player", __name__)


def getToken():
    return (
        request.args.get("token")
        or (
            request.headers["Authorization"][7:]
            if "Authorization" in request.headers
            else None
        )
        or generateToken(getUID())
    )


@player.route("start", methods=["POST"])
def startPlayer():
    reqData = json.loads(request.data)
    reqData.update(request.args)
    checkArgs(["mediaType", "mediaData"], reqData)
    uid = getUID()
    logger.info("Starting transcoder for user " + str(uid))
    deviceData = {}

    if "idDevice" in reqData and int(reqData["idDevice"]) != -1:
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "SELECT * FROM devices WHERE idDevice = %(idDevice)s",
            {"idDevice": reqData["idDevice"]},
        )
        data = cursor.fetchone()
        sqlConnection.close()
        if data["enabled"] == 0:
            return False
        dev = importDevice(data["type"])
        device = dev(
            uid,
            getToken(),
            data["address"],
            data["port"],
            data["user"],
            data["password"],
            data["device"],
        )
        deviceData["data"], startData = device.playMedia(
            int(reqData["mediaType"]),
            int(reqData["mediaData"]),
            reqData,
        )
        deviceData["settings"] = data
        if hasattr(device, "doWork"):
            doWork(device)
    else:
        deviceData = None
        obj = transcoder(int(reqData["mediaType"]), int(reqData["mediaData"]))
        obj.enableHLS(True, configData["config"]["hlsTime"])
        obj.configure(reqData)
        startData = obj.start()

    r_userFiles.set(
        uid,
        json.dumps(
            {
                "mediaType": reqData["mediaType"],
                "mediaData": reqData["mediaData"],
                "transcoder": startData,
                "device": deviceData,
            }
        ),
    )
    return jsonify({"status": "ok", "data": "ok"})


@thread
def doWork(obj: PlayerBase):
    obj.doWork()


@player.route("subtitle/<int:mediaType>/<mediaData>/stream/<int:subStream>", methods=["GET"])
@player.route("subtitle/<int:mediaType>/<mediaData>/file/<subFile>", methods=["GET"])
def getSubtitles(mediaType: int, mediaData: str, subStream = None, subFile = None):
    obj = transcoder(int(mediaType), mediaData)

    if "startFrom" in request.args:
        obj.setStartTime(request.args['startFrom'])

    if subStream is not None:
        obj.setSubStream(subStream)
    else:
        obj.setSubFile(subFile)
    
    return Response(obj.getSubtitles(), mimetype="text/vtt")


@player.route("status", methods=["GET"])
def getTranscoderStatus():
    uid = getUID()
    data = r_userFiles.get(uid)
    if data is not None:
        data = json.loads(data)
        if os.path.exists(data["transcoder"]["outDir"]):
            if data["transcoder"] != {}:
                if os.path.exists(
                    data["transcoder"]["outDir"] + "/stream.m3u8"
                ) and os.path.exists(data["transcoder"]["outDir"] + "/stream001.ts"):
                    return jsonify(
                        {"status": "ok", "data": {"available": True, "running": True}}
                    )
                else:
                    return jsonify(
                        {"status": "ok", "data": {"available": False, "running": True}}
                    )
            else:
                return jsonify(
                    {"status": "ok", "data": {"available": True, "running": False}}
                )
        else:
            return jsonify({"status": "ok", "data": {"available": False, "running": False}})
    else:
        return jsonify({"status": "ok", "data": {"available": False, "running": False}})


@player.route("m3u8", methods=["GET"])
def getTranscoderM3U8():
    token = getToken()
    uid = getUID()
    # static files are directly served by nginx
    fileUrl = configData["config"]["baseUrl"] + "/out/" + str(uid) + "/"
    # add time to fileUrl prevent browser caching
    fileUrlEnd = "?token=" + token + "&time=" + str(time.time())
    dat = ""

    file = os.path.join(configData["config"]["outDir"], str(getUID()), "stream.m3u8")
    if os.path.exists(file):
        fileData = open(file, "r").read()
        for i in fileData.split("\n"):
            if ".ts" in i and "stream" in i:
                dat += fileUrl + i + fileUrlEnd + "\n"
            else:
                dat += i + "\n"
        return Response(dat, mimetype="application/x-mpegURL")
    else:
        abort(404)


@player.route("file/<int:mediaType>/<mediaData>", methods=["GET"])
def player_getFile(mediaType: int, mediaData: str):
    path = getMediaPath(
        int(mediaType), mediaData, False
    )
    uid = getUID()
    r_userFiles.set(
        uid,
        json.dumps(
            {
                "mediaType": mediaType,
                "mediaData": mediaData,
                "transcoder": {},
                "device": {},
            }
        ),
    )
    return jsonify(
        {
            "status": "ok",
            "data": (
                configData["config"]["baseUrl"].encode("utf-8")
                + b"/content/"
                + path
                + b"?token="
                + (getToken()).encode("utf-8")
            ).decode("utf-8"),
        }
    )
    #    return getFile(path, "video")


@player.route("property/<int:mediaType>/<mediaData>", methods=["GET"])
def player_getFileInfos(mediaType: int, mediaData: str):
    sqlConnection, cursor = getSqlConnection()
    st = 0
    if mediaType == 1 or mediaType == 3:
        cursor.execute(
            "SELECT watchTime FROM status WHERE idUser = %(idUser)s AND mediaType = %(mediaType)s AND idMedia = %(idMedia)s;",
            {
                "idUser": getUID(),
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

@player.route("property/<int:mediaType>/<mediaData>", methods=["PUT"])
def player_setFileInfos(mediaType: int, mediaData: str):
    checkUser("admin")
    idVid = getIdVid(mediaType, mediaData)

    allowedFields = [
        "idLib",
        "path",
        "format",
        "duration",
        "extension",
        "stereo3d",
        "ratio",
        "dimension",
        "pix_fmt",
        "video_codec",
        "size"
    ]
    sqlConnection, cursor = getSqlConnection()
    data = json.loads(request.data)
    err = False
    msg = ""

    for i, val in data.items():
        if i in allowedFields:
            if i == "idLib" and not checkLibraryType(val, mediaType):
                err = True
                msg = "Invalid library type"
                break

            cursor.execute(
                "UPDATE video_files SET " + i + " = %(val)s WHERE idVid = %(idVid)s",
                {"val": val, "idVid": idVid})
        else:
            err = True
            msg = "Unknown field"
            break

    if not err:
        sqlConnection.commit()
    sqlConnection.close()

    if not err:
        return jsonify({"status": "ok", "data": "ok"})
    else:
        return jsonify({"status": "err", "data": msg}), 400


@player.route("stop", methods=["GET"])
def player_stop():
    checkArgs(["endTime"])
    uid = getUID()
    endTime = float(request.args["endTime"])    

    logger.info("Stopping transcoder for user " + str(uid))

    fileData = r_userFiles.get(uid)
    if fileData is not None:
        fileData = json.loads(fileData)

        if fileData["device"] is not None:
            # stop device
            data = fileData["device"]["settings"]
            if data["enabled"] != 0:
                dev = importDevice(data["type"])
                device = dev(
                    uid,
                    getToken(),
                    data["address"],
                    data["port"],
                    data["user"],
                    data["password"],
                    data["device"],
                )
                device.stop()

        # set watch time
        player_setWatchTime(uid, fileData["mediaType"], fileData["mediaData"], endTime)
        # stop transcoder
        transcoder.stop(fileData["transcoder"])

    r_userFiles.delete(uid)

    return jsonify({"status": "ok", "data": "ok"})


def player_setWatchTime(uid: str, mediaType: int, idMedia: int, endTime: float):
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
