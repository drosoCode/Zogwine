import json

from app.devices.PlayerBase import PlayerBase
from app.files import getOutputDir, getMediaFromUrl
from app.socketio import sio
from app.dbHelper import r_remotePlayer, configData, getSqlConnection
from app.utils import getUID, checkUser

defaultDict = {
    "status": 0,
    "position": 0,
    "mediaType": -1,
    "mediaData": "-1",
}


def getPlayerID(uid, name=None):
    if name is not None and name != "self":
        if checkUser("cast", False, uid):
            sqlConnection, cursor = getSqlConnection()
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM devices WHERE type = 'web' AND address = %(name)s",
                {"name": name},
            )
            data = cursor.fetchone()
            sqlConnection.close()
            if data["cnt"] == 1:
                return str(name)
        else:
            return False
    return str(uid)


@sio.event
def remote_player(sid, message):
    playerID = getPlayerID(getUID(sid), message.get("name"))

    if message["action"] == "connect":
        if playerID is not None:
            data = {"sid": sid}
            data.update(defaultDict)
            r_remotePlayer.set(
                playerID,
                json.dumps(data),
            )
            sio.emit(
                "remote_player",
                json.dumps(
                    {"type": "status", "data": "ok", "action": message["action"]}
                ),
                room=sid,
            )
        else:
            sio.emit(
                "remote_player",
                json.dumps(
                    {"type": "status", "data": "error", "action": message["action"]}
                ),
                room=sid,
            )
    elif message["action"] in ["status", "position"]:
        d = r_remotePlayer.get(playerID)
        if d:
            d = json.loads(d.decode("utf-8"))

            d[message["action"]] = message["data"]

            r_remotePlayer.set(
                playerID,
                json.dumps(d),
            )


@sio.event
def disconnect(sid):
    for i in r_remotePlayer.scan_iter():
        d = r_remotePlayer.get(i)
        if json.loads(d.decode("utf-8"))["sid"] == sid:
            r_remotePlayer.delete(i)


class web(PlayerBase):
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
        self._id = getPlayerID(uid, address)
        self._data = False

        if self._id:
            self._data = r_remotePlayer.get(self._id) or False
            if self._data:
                self._data = json.loads(self._data.decode("utf-8"))

    def playMedia(self, mediaType: int, mediaData: str, args: dict = None) -> tuple:
        if self._data:
            playData = {"mediaType": mediaType, "mediaData": mediaData}
            playData.update(args)

            self._data.update({"mediaType": mediaType, "mediaData": mediaData})
            r_remotePlayer.set(
                self._id,
                json.dumps(self._data),
            )

            sio.emit(
                "remote_player",
                json.dumps(
                    {
                        "type": "action",
                        "data": playData,
                        "action": "playMedia",
                    }
                ),
                room=self._data["sid"],
            )
        return {}, {}

    def seek(self, pos: int):
        if not self._data:
            return False

        self._data.update({"position": pos})
        r_remotePlayer.set(
            self._id,
            json.dumps(self._data),
        )

        sio.emit(
            "remote_player",
            json.dumps(
                {
                    "type": "action",
                    "data": pos,
                    "action": "seek",
                }
            ),
            room=self._data["sid"],
        )

    def play(self):
        if not self._data:
            return False

        self._data.update({"status": 2})
        r_remotePlayer.set(
            self._id,
            json.dumps(self._data),
        )

        sio.emit(
            "remote_player",
            json.dumps({"type": "action", "action": "play"}),
            room=self._data["sid"],
        )

    def pause(self):
        if not self._data:
            return False

        self._data.update({"status": 1})
        r_remotePlayer.set(
            self._id,
            json.dumps(self._data),
        )

        sio.emit(
            "remote_player",
            json.dumps({"type": "action", "action": "pause"}),
            room=self._data["sid"],
        )

    def stop(self):
        if not self._data:
            return False

        self._data.update(defaultDict)
        r_remotePlayer.set(
            self._id,
            json.dumps(self._data),
        )

        sio.emit(
            "remote_player",
            json.dumps({"type": "action", "action": "stop"}),
            room=self._data["sid"],
        )

    @property
    def position(self) -> float:
        if self._data:
            return self._data["position"]
        else:
            return False

    @property
    def status(self) -> int:
        if self._data:
            return self._data["status"]
        else:
            return False

    @property
    def playingMedia(self) -> tuple:
        if not self._data or self._data["mediaType"] == -1:
            return None
        return {
            "mediaType": self._data["mediaType"],
            "mediaData": str(self._data["mediaData"]),
        }

    @property
    def available(self) -> bool:
        if self._data:
            return True
        else:
            return False
