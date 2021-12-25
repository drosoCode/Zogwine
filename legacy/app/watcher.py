from uwsgidecorators import thread
import time
import os
import json
from .dbHelper import r_userFiles, configData
from .log import logger
from .transcoder import transcoder


@thread
def startWatcher():
    if not os.path.exists("/tmp/zogwine/ffmpeg/"):
        os.makedirs("/tmp/zogwine/ffmpeg/")
    sleepTime = configData["config"]["checkInterval"]

    while True:
        checkTranscodingErrors()
        time.sleep(sleepTime)


def checkTranscodingErrors():
    # search for errors after transcoder start, and try to fall back to libx264
    for u in r_userFiles.scan_iter():
        data = r_userFiles.get(u)
        if data is not None:
            data = json.loads(data)
            if "logFile" in data["transcoder"] and os.path.exists(
                data["transcoder"]["logFile"]
            ):
                with open(data["transcoder"]["logFile"], "r") as f:
                    d = ("".join(f.readlines())).lower()
                    if "error" in d or "failed" in d:
                        logger.error(
                            ("ffmpeg error, restarting ... [" + d + "]").encode("utf-8")
                        )
                        killAndRestart(
                            data,
                            transcoder.fromJSON(data["transcoder"]["classData"]),
                            u,
                        )
                    elif (
                        "startTime" in data
                        and data["startTime"] + configData["hlsKill"] <= time.time()
                    ):
                        tr = transcoder.fromJSON(data["transcoder"]["classData"])
                        if tr._enableHLS:
                            killAndRestart(data, tr, u)


def killAndRestart(data, tr, uid):
    transcoder.stop(data["transcoder"])
    if tr._startNum <= 0:
        tr._startNum = 1
        tr._encoder = "libx264"
        startData = tr.start()
        r_userFiles.set(
            uid,
            json.dumps(
                {
                    "mediaType": data["mediaType"],
                    "mediaData": data["mediaData"],
                    "transcoder": startData,
                    "device": data["device"] or {},
                }
            ),
        )
    else:
        r_userFiles.delete(uid)
