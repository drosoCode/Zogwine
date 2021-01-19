import requests
import time
import urllib.parse
import os

from app.devices.PlayerBase import PlayerBase
from app.transcoder import transcoder
from app.dbHelper import configData
from app.log import logger
from app.files import getOutputDir


class xbmc4xbox(PlayerBase):
    def __init__(
        self,
        uid: int,
        token: str,
        address: str,
        port: int = None,
        user: str = None,
        password: str = None,
        device: str = None,
    ):
        self._token = token
        self._outDir = getOutputDir()
        self._endpoint = "http://" + str(address) + "/xbmcCmds/xbmcHttp?command="
        if user is not None and password is not None:
            self._auth = (str(user), str(password))
        else:
            self._auth = None
        self._baseUrl = configData["config"]["baseUrl"] + "/out/" + str(uid) + "/"
        self._startData = None

    def activePid(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def playMedia(self, mediaType: int, mediaData: int, data: dict = None):
        obj = transcoder(int(mediaType), int(mediaData))
        obj.enableHLS(True)
        obj.configure(data)
        if int(obj._resize) > 720 or int(obj._resize) < 0:
            obj.resize(720)
        self._startData = obj.start()
        return self._startData

    def doWork(self):
        d = os.listdir(self._outDir)
        while "stream001.ts" not in d:
            time.sleep(2)
            d = os.listdir(self._outDir)

        logger.info("STARTING XBMC4XBOX Player")
        logger.debug(
            requests.get(self._endpoint + "ClearPlayList(1)", auth=self._auth).text
        )
        logger.debug(
            requests.get(
                self._endpoint
                + "AddToPlayList("
                + urllib.parse.quote(
                    self._baseUrl + "stream000.ts?token=" + self._token, safe=""
                )
                + ";1)",
                auth=self._auth,
            ).text
        )
        logger.debug(
            requests.get(self._endpoint + "SetCurrentPlaylist(1)", auth=self._auth).text
        )
        logger.debug(requests.get(self._endpoint + "PlayNext()", auth=self._auth).text)

        logger.debug("STARTING XBMC4XBOX Main Loop")
        prev = 0
        dowork = True
        while dowork:
            d = sorted(os.listdir(self._outDir))
            num = -1
            for i in range(len(d) - 1, 0, -1):
                if d[i][len(d[i]) - 2 :] == "ts":
                    num = d[i]
                    num = num[6 : len(num) - 3]
                    break

            if int(num) > prev:
                logger.debug("Add stream: " + num)
                logger.debug(
                    requests.get(
                        self._endpoint
                        + "AddToPlayList("
                        + urllib.parse.quote(
                            self._baseUrl + "stream" + num + ".ts?token=" + self._token,
                            safe="",
                        )
                        + ";1)",
                        auth=self._auth,
                    ).text
                )
                prev = int(num)
            time.sleep(1)
            dowork = self.activePid(self._startData["pid"])

    def seek(self, pos: int):
        pass

    def play(self):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    def mute(self):
        pass

    def unmute(self):
        pass

    def volume(self, volume: int):
        pass

    def _position(self) -> float:
        pass

    @property
    def _volume(self) -> int:
        pass

    @property
    def _status(self) -> str:
        pass