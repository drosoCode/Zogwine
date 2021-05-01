import requests
import os
import time
import json

from app.devices.PlayerBase import PlayerBase
from app.transcoder import transcoder
from app.dbHelper import configData
from app.files import getOutputDir, getMediaFromUrl


class kodi(PlayerBase):
    def __init__(
        self,
        uid: int,
        token: str,
        address: str,
        port: int = None,
        user: str = None,
        password: str = None,
        device: str = None,
        skipInit: bool = False,
    ):
        super().__init__(uid, token, address, port, user, password, device)
        self._port = str(port or 80)
        self._outDir = getOutputDir()
        self._url = (
            configData["config"]["baseUrl"] + "/api/player/m3u8?token=" + str(token)
        )
        self._playerid = 1
        if user is not None and password is not None:
            self._auth = (str(user), str(password))
        else:
            self._auth = None

    @property
    def available(self) -> bool:
        try:
            r = requests.post(
                "http://" + self._address + ":" + self._port + "/jsonrpc",
                data=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "JSONRPC.Ping",
                        "id": 1,
                    }
                ),
                auth=self._auth,
                headers={"Content-Type": "application/json"},
                timeout=3,
            )
            return r.status_code == 200 and json.loads(r.text)["result"] == "pong"
        except:
            return False

    def playMedia(self, mediaType: int, mediaData: int, data: dict = None) -> tuple:
        if not self.available:
            return False
        obj = transcoder(int(mediaType), int(mediaData))
        obj.enableHLS(True)
        obj.configure(data)
        return {}, obj.start()

    def _request(self, params):
        return requests.post(
            "http://" + self._address + ":" + self._port + "/jsonrpc",
            data=json.dumps(params),
            auth=self._auth,
            headers={"Content-Type": "application/json"},
        ).text

    def doWork(self):
        if not self.available:
            return False
        d = os.listdir(self._outDir)
        while "stream001.ts" not in d:
            time.sleep(2)
            d = os.listdir(self._outDir)

        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Player.Open",
                "params": {"item": {"file": self._url}},
                "id": 1,
            }
        )

    def seek(self, value: int):
        if not self.available:
            return False
        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Player.Seek",
                "params": {"playerid": self._playerid, "time": value},
                "id": 1,
            }
        )

    def play(self):
        if not self.available:
            return False
        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Player.PlayPause",
                "params": {"playerid": self._playerid, "play": True},
                "id": 1,
            }
        )

    def pause(self):
        if not self.available:
            return False
        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Player.PlayPause",
                "params": {"playerid": self._playerid, "play": False},
                "id": 1,
            }
        )

    def stop(self):
        if not self.available:
            return False
        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Player.Stop",
                "params": {"playerid": self._playerid},
                "id": 1,
            }
        )

    def mute(self):
        if not self.available:
            return False
        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Application.SetMute",
                "params": {"mute": True},
                "id": 1,
            }
        )

    def unmute(self):
        if not self.available:
            return False
        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Application.SetMute",
                "params": {"mute": False},
                "id": 1,
            }
        )

    def setVolume(self, value: int):
        if not self.available:
            return False
        self._request(
            {
                "jsonrpc": "2.0",
                "method": "Application.SetVolume",
                "params": {"volume": str(value)},
                "id": 1,
            }
        )

    @property
    def position(self) -> float:
        if not self.available:
            return False
        d = json.loads(
            self._request(
                {
                    "jsonrpc": "2.0",
                    "method": "Player.GetProperties",
                    "params": {"playerid": 1, "properties": ["time"]},
                    "id": 1,
                }
            )
        )
        if "result" in d and "time" in d["result"]:
            return (
                d["result"]["time"]["hours"] * 3600
                + d["result"]["time"]["minutes"] * 60
                + d["result"]["time"]["seconds"]
            )
        else:
            return 0

    @property
    def loaded(self) -> float:
        if not self.available:
            return False
        d = json.loads(
            self._request(
                {
                    "jsonrpc": "2.0",
                    "method": "Player.GetProperties",
                    "params": {
                        "playerid": 1,
                        "properties": ["cachepercentage", "totaltime"],
                    },
                    "id": 1,
                }
            )
        )
        if (
            "result" in d
            and "totaltime" in d["result"]
            and "cachepercentage" in d["result"]
        ):
            return round(
                d["result"]["cachepercentage"]
                * (
                    d["result"]["totaltime"]["hours"] * 3600
                    + d["result"]["totaltime"]["minutes"] * 60
                    + d["result"]["totaltime"]["seconds"]
                )
            )
        else:
            return 0

    @property
    def volume(self) -> int:
        if not self.available:
            return False
        d = json.loads(
            self._request(
                {
                    "jsonrpc": "2.0",
                    "method": "Application.GetProperties",
                    "params": {"properties": ["volume"]},
                    "id": 1,
                }
            )
        )
        if "result" in d and "volume" in d["result"]:
            return d["result"]["volume"]
        else:
            return 0

    @property
    def status(self) -> int:
        if not self.available:
            return 0
        d = json.loads(
            self._request(
                {
                    "jsonrpc": "2.0",
                    "method": "Player.GetProperties",
                    "params": {
                        "playerid": self._playerid,
                        "properties": ["speed"],
                    },
                    "id": 1,
                }
            )
        )
        if "result" not in d or "speed" not in d["result"]:
            return 0
        elif d["result"]["speed"] == 0:
            return 1
        else:
            return 2

    @property
    def playingMedia(self) -> tuple:
        if not self.available:
            return None
        d = json.loads(
            self._request(
                {
                    "jsonrpc": "2.0",
                    "method": "Player.GetItem",
                    "params": {
                        "playerid": self._playerid,
                        "properties": ["file"],
                    },
                    "id": 1,
                }
            )
        )
        if "result" in d and "file" in d["result"]:
            return getMediaFromUrl(d["result"]["file"])
        else:
            return None