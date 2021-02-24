import requests
import time
import urllib.parse
import os

from app.devices.PlayerBase import PlayerBase
from app.transcoder import transcoder
from app.dbHelper import configData
from app.log import logger
from app.files import getOutputDir, getMediaFromUrl


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
        super().__init__(uid, token, address, port, user, password, device)
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

    def playMedia(self, mediaType: int, mediaData: int, data: dict = None) -> tuple:
        obj = transcoder(int(mediaType), int(mediaData))
        obj.enableHLS(True)
        obj.configure(data)
        if int(obj._resize) > 720 or int(obj._resize) < 0:
            obj.resize(720)
        self._startData = obj.start()
        return {}, self._startData

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
        data = requests.get(
            self._endpoint + "GetCurrentlyPlaying", auth=self._auth
        ).text
        url = data[20 : data.find("\n", 20)]
        currentStream = int(url[url.find("/stream") + 7 : url.find(".ts?token=")])

        data = requests.get(
            self._endpoint + "GetPlaylistContents(1)", auth=self._auth
        ).text
        urls = data[12 : len(data) - 8].split("\n<li>")

        posStream = pos // configData["config"]["hlsTime"]

        if pos < configData["config"]["hlsTime"] * currentStream:
            for i in range(currentStream - posStream):
                requests.get(self._endpoint + "PlayPrev()", auth=self._auth)
        else:
            playlistNum = len(urls) - posStream
            if playlistNum < 0:
                for i in range(len(urls) - 1 - currentStream):
                    requests.get(self._endpoint + "PlayNext()", auth=self._auth)
            else:
                for i in range(posStream - currentStream):
                    requests.get(self._endpoint + "PlayNext()", auth=self._auth)

        percent = round(
            (pos % configData["config"]["hlsTime"])
            / configData["config"]["hlsTime"]
            * 100
        )
        requests.get(
            self._endpoint + "SeekPercentage(" + str(percent) + ")", auth=self._auth
        )

    def play(self):
        requests.get(self._endpoint + "Action(79)", auth=self._auth).text

    def pause(self):
        requests.get(self._endpoint + "Pause()", auth=self._auth).text

    def stop(self):
        requests.get(self._endpoint + "Stop()", auth=self._auth).text

    def mute(self):
        requests.get(self._endpoint + "Mute()", auth=self._auth).text

    def unmute(self):
        requests.get(self._endpoint + "Mute()", auth=self._auth).text

    def setVolume(self, volume: int) -> bool:
        if volume > 100 or volume < 0:
            return False
        requests.get(
            self._endpoint + "SetVolume(" + str(volume) + ")", auth=self._auth
        ).text
        return True

    @property
    def position(self) -> float:
        data = requests.get(
            self._endpoint + "GetCurrentlyPlaying", auth=self._auth
        ).text
        url = data[20 : data.find("\n", 20)]

        nb = int(url[url.find("/stream") + 7 : url.find(".ts?token=")])

        p = data.find("Percentage") + 11
        percentage = int(data[p : data.find("\n", p)])

        return configData["config"]["hlsTime"] * nb + configData["config"][
            "hlsTime"
        ] * (percentage / 100)

    @property
    def loaded(self):
        data = requests.get(
            self._endpoint + "GetPlaylistContents(1)", auth=self._auth
        ).text
        urls = data[12 : len(data) - 8].split("\n<li>")
        return len(urls) * configData["config"]["hlsTime"]

    @property
    def volume(self) -> int:
        data = requests.get(self._endpoint + "GetVolume", auth=self._auth).text
        return int(data[11 : data.find("</html>")])

    @property
    def status(self) -> int:
        data = requests.get(
            self._endpoint + "GetCurrentlyPlaying", auth=self._auth
        ).text
        p = data.find("PlayStatus") + 11
        s = data[p : data.find("\n", p)]

        if s == "Playing":
            return 2
        elif s == "Paused":
            return 1
        else:
            return 0

    @property
    def playingMedia(self) -> tuple:
        data = requests.get(
            self._endpoint + "GetCurrentlyPlaying", auth=self._auth
        ).text
        return getMediaFromUrl(data[20 : data.find("\n", 20)])