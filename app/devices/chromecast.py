import pychromecast
import os
import time

from app.devices.PlayerBase import PlayerBase
from app.transcoder import transcoder
from app.dbHelper import configData
from app.files import getOutputDir, getMediaFromUrl


class chromecast(PlayerBase):
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
        self._outDir = getOutputDir(uid)
        self._url = (
            configData["config"]["baseUrl"] + "/api/player/m3u8?token=" + str(token)
        )
        try:
            self._cast = pychromecast.Chromecast(str(address))
            self._cast.wait()
            self._mc = self._cast.media_controller
        except:
            self._cast = None

    def playMedia(self, mediaType: int, mediaData: int, data: dict = None) -> tuple:
        if self._cast:
            return False
        obj = transcoder(int(mediaType), int(mediaData))
        obj.enableHLS(True)
        obj.configure(data)
        return {}, obj.start()

    def doWork(self):
        if self._cast:
            return False
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
        if self._cast:
            return False
        self._mc.seek(pos)

    def play(self):
        if self._cast:
            return False
        self._mc.play()

    def pause(self):
        if self._cast:
            return False
        self._mc.pause()

    def stop(self):
        if self._cast:
            return False
        self._mc.block_until_active()
        self._mc.stop()

    def mute(self):
        if self._cast:
            return False
        self._cast.set_volume_muted(True)

    def unmute(self):
        if self._cast:
            return False
        self._cast.set_volume_muted(False)

    def setVolume(self, volume: int):
        if self._cast:
            return False
        self._cast.set_volume(volume)

    @property
    def position(self) -> float:
        if self._cast:
            return False
        self._mc.block_until_active()
        return self._mc.status.current_time

    @property
    def volume(self) -> int:
        if self._cast:
            return False
        self._mc.block_until_active()
        return self._cast.status.volume_level

    @property
    def status(self) -> int:
        if self._cast:
            return False
        self._mc.block_until_active()
        s = self._mc.status.player_state
        if s == "PLAYING":
            return 2
        elif s == "PAUSED":
            return 1
        else:
            return 0

    @property
    def playingMedia(self) -> tuple:
        if self._cast:
            return None
        return getMediaFromUrl(self._mc.status.content_id)
