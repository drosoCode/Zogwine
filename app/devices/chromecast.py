import pychromecast
import os
import time

from app.devices.PlayerBase import PlayerBase
from app.transcoder import transcoder
from app.dbHelper import configData


class chromecast(PlayerBase):
    def __init__(
        self,
        token: str,
        address: str,
        port: int = None,
        user: str = None,
        password: str = None,
        device: str = None,
    ):
        self._outDir = "out/" + token
        self._url = (
            configData["config"]["baseUrl"] + "/api/player/m3u8?token=" + str(token)
        )
        self._cast = pychromecast.Chromecast(str(address))
        self._cast.wait()
        self._mc = self._cast.media_controller

    def playMedia(self, obj):
        return obj.start()

    def doWork(self):
        d = os.listdir(self._outDir)
        while "stream001.ts" not in d:
            time.sleep(2)
            d = os.listdir(self._outDir)

        self._mc.play_media(
            self._url,
            "video/mp4",
        )
        self._mc.play()

    def seek(self, pos: int):
        self._mc.seek(pos)

    def play(self):
        self._mc.play()

    def pause(self):
        self._mc.pause()

    def stop(self):
        self._mc.block_until_active()
        self._mc.stop()

    def mute(self):
        self._cast.set_volume_muted(True)

    def unmute(self):
        self._cast.set_volume_muted(False)

    def setVolume(self, volume: int):
        self._cast.set_volume(volume)

    @property
    def position(self) -> float:
        self._mc.block_until_active()
        return self._mc.status.current_time

    @property
    def volume(self) -> int:
        self._mc.block_until_active()
        return self._cast.status.volume_level

    @property
    def status(self) -> int:
        self._mc.block_until_active()
        s = self._mc.status.player_state
        if s == "PLAYING":
            return 2
        elif s == "PAUSED":
            return 1
        else:
            return 0

    @property
    def playingMedia(self) -> str:
        return self._mc.status.content_id
