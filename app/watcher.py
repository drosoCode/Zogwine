from uwsgidecorators import thread
import time
import os
import json
import jsonpickle
import signal
import croniter
import datetime

from .dbHelper import r_userFiles, configData
from .log import logger
from .transcoder import transcoder

from .movie import mov_runScan
from .tvs import tvs_runScan, tvs_runUpcomingScan
from .core import refreshCache, runPeopleScan


@thread
def startWatcher():
    if not os.path.exists("/tmp/zogwine/ffmpeg/"):
        os.makedirs("/tmp/zogwine/ffmpeg/")

    cronData = setupCron(configData["cron"])
    sleepTime = configData["config"]["checkInterval"]
    lastCheck = 0

    while True:
        checkTranscodingErrors()
        if lastCheck + 60 <= time.time():
            # check only once per minute
            lastCheck = time.time()
            checkCron(cronData)
        time.sleep(sleepTime)


def checkTranscodingErrors():
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
                        if tr._startNum <= 0:
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
                                        "device": data["device"] or {},
                                    }
                                ),
                            )
                        else:
                            r_userFiles.delete(u)


def setupCron(cron):
    cronData = []
    now = datetime.datetime.now()
    for k in cron.keys():
        if cron[k] != "":
            cr = croniter.croniter(cron[k], now)
            cronData.append([k, cr, cr.get_next(datetime.datetime)])
    return cronData


def checkCron(cronData):
    now = datetime.datetime.now()
    for i in range(len(cronData)):
        if cronData[i][2] <= now:
            execCronProcess(cronData[i][0])
            cronData[i][2] = cronData[i][1].get_next(datetime.datetime)


def execCronProcess(name):
    logger.info("[CRON] running " + name)
    if name == "tvs":
        tvs_runScan()
    elif name == "movie":
        mov_runScan()
    elif name == "upcomingEpisode":
        tvs_runUpcomingScan()
    elif name == "cache":
        refreshCache()
    elif name == "person":
        runPeopleScan()
