from uwsgidecorators import thread
import time
import os
import json
import jsonpickle
import signal

from .dbHelper import r_userFiles
from .log import logger
from .transcoder import transcoder


@thread
def startWatcher():
    if not os.path.exists("/tmp/zogwine/ffmpeg/"):
        os.makedirs("/tmp/zogwine/ffmpeg/")
    while True:
        checkTranscodingErrors()
        time.sleep(5)


def checkTranscodingErrors():
    print("checking")
    # search for errors the 2 first minutes after transcoder start, and try to fall back to libx264
    for u in r_userFiles.scan_iter():
        data = r_userFiles.get(u)
        if data is not None:
            data = json.loads(data)
            if "logFile" in data["transcoder"] and os.path.exists(
                data["transcoder"]["logFile"]
            ):
                with open(data["transcoder"]["logFile"], "r") as f:
                    d = "".join(f.readlines())
                    if "error" in d or "failed" in d:
                        logger.error(
                            ("ffmpeg error, restarting ... [" + d + "]").encode("utf-8")
                        )
                        transcoder.stop(data["transcoder"])
                        tr = jsonpickle.decode(data["transcoder"]["classData"])
                        if tr._startNum == 0:
                            tr._startNum = 1
                            tr._encoder = "libx264"
                            startData = tr.start()
                            r_userFiles.set(
                                u,
                                json.dumps(
                                    {
                                        "mediaType": data["mediaType"],
                                        "mediaData": data["mediaData"],
                                        "transcoder": startData,
                                        "device": data["deviceData"],
                                    }
                                ),
                            )
