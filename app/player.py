import time
from flask import request, Blueprint, jsonify, abort, Response, send_file
import redis
import os

from transcoder import transcoder
from log import logger
from utils import checkArgs, getFile, getMediaPath

from dbHelper import getSqlConnection, r_userFiles, r_userTokens, configData

player = Blueprint("player", __name__)
allowedMethods = ["GET", "POST"]


@player.route("/api/player/start")
def startPlayer():
    uid = r_userTokens.get(request.args["token"])
    logger.info("Starting transcoder for user " + str(uid))
    obj = transcoder.fromJSON(r_userFiles.get(uid))

    obj.enableHLS(True, configData["config"]["hlsTime"])
    if "audioStream" in request.args:
        obj.setAudioStream(request.args.get("audioStream"))
    if "subStream" in request.args:
        obj.setSub(request.args.get("subStream"))
    if "startFrom" in request.args:
        obj.setStartTime(request.args.get("startFrom"))
    if "resize" in request.args:
        obj.resize(request.args.get("resize"))
    if "remove3D" in request.args:
        r3 = request.args["remove3D"]
        if r3 == "tab" or r3 == "sbs":
            obj.remove3D(r3)

    obj.start()

    r_userFiles.set(uid, obj.toJSON())
    return jsonify({"status": "ok", "data": "ok"})


@player.route("/api/player/m3u8")
def getTranscoderM3U8():
    token = request.args["token"]
    # add time to fileUrl prevent browser caching
    fileUrl = "/api/player/file?token=" + token + "&time=" + str(time.time()) + "&name="
    dat = ""

    file = "../out/" + str(token) + "/stream.m3u8"
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


@player.route("/api/player/file")
def getTranscoderFile():
    name = request.args["name"]
    token = request.args["token"]
    # send transcoded file
    file = "../out/" + str(token) + "/" + name
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


@player.route("/api/player/getFile")
def player_getFile():
    checkArgs(["mediaType", "mediaData"])
    path = getMediaPath(
        request.args["token"], request.args["mediaType"], request.args["mediaData"]
    )
    if os.path.exists(path):
        return getFile(path, "video")
    else:
        abort(404)


def getFileInfos(token, mediaType, mediaData):
    sqlConnection, cursor = getSqlConnection()
    uid = r_userTokens.get(token)
    path = getMediaPath(token, mediaType, mediaData)
    logger.info(
        "Media path for type: "
        + str(mediaType)
        + " and id: "
        + str(mediaData)
        + " -> "
        + str(path)
    )
    tr = transcoder(
        path,
        configData["config"]["outDir"] + "/" + token,
        configData["config"]["encoder"],
        configData["config"]["crf"],
    )

    # get last view end if available
    st = None
    if mediaType == 1 or mediaType == 3:
        cursor.execute(
            "SELECT watchTime FROM status WHERE idUser = %(idUser)s AND mediaType = %(mediaType)s AND idMedia = %(idMedia)s;",
            {
                "idUser": r_userTokens.get(token),
                "mediaType": mediaType,
                "idMedia": mediaData,
            },
        )
        data = cursor.fetchone()
        if data != None and "viewTime" in data:
            st = float(data["viewTime"])

    if st is not None:
        tr.setStartTime(st)

    r_userFiles.set(uid, tr.toJSON())
    res = tr.getFileInfos()
    sqlConnection.close()
    return res


@player.route("/api/player/getInfos", methods=allowedMethods)
def player_getFileInfos():
    checkArgs(["mediaType", "mediaData"])
    return jsonify(
        {
            "status": "ok",
            "data": getFileInfos(
                request.args["token"],
                request.args["mediaType"],
                request.args["mediaData"],
            ),
        }
    )


@player.route("/api/player/stop", methods=allowedMethods)
def player_stop():
    token = request.args["token"]
    mediaType = request.args["mediaType"]
    mediaData = request.args["mediaData"]
    endTime = request.args.get("endTime")
    # set watch time
    player_setWatchTime(token, mediaType, mediaData, endTime)
    # stop transcoder
    logger.info("Stopping transcoder for user " + str(r_userTokens.get(token)))

    uid = r_userTokens.get(token)
    obj = transcoder.fromJSON(r_userFiles.get(uid))
    obj.stop()
    del obj
    r_userFiles.delete(uid)

    return jsonify({"status": "ok", "data": "ok"})


def player_setWatchTime(token, mediaType, idMedia, endTime=None):
    uid = r_userTokens.get(token)
    if endTime is not None:
        sqlConnection, cursor = getSqlConnection()
        tr = transcoder.fromJSON(r_userFiles.get(uid))

        endTime = tr.getWatchedDuration(endTime)
        duration = float(tr.getFileInfos()["general"]["duration"])

        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute(
            "SELECT idStatus, watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = %(mediaType)s AND idMedia = %(idMedia)s;",
            {"idUser": uid, "mediaType": mediaType, "idMedia": idMedia},
        )
        data = cursor.fetchone()
        viewAdd = 0

        if endTime > duration * configData["config"]["watchedThreshold"]:
            viewAdd = 1

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
        sqlConnection.close()

        return True
    else:
        return False
