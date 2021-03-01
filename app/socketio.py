import socketio
import json

from .log import logger
from .dbHelper import r_userTokens, configData
from .utils import getUID
from .user import signout

mgr = socketio.RedisManager(
    "redis://"
    + configData["redis"]["host"]
    + ":"
    + str(configData["redis"]["port"])
    + "/"
    + str(configData["redis"]["websocketsDB"])
)
sio = socketio.Server(
    async_mode="gevent_uwsgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    client_manager=mgr,
)


@sio.event
def connect(sid, environ):
    logger.info("New WS socket connected: " + sid)


@sio.event
def disconnect(sid):
    logger.info("WS socket disconnected: " + sid)


@sio.event
def authentication(sid, message):
    if message["action"] == "login":
        r_userTokens.set(str(sid), getUID(message["data"]))
    else:
        signout(sid)
    sio.emit(
        "authentication",
        json.dumps({"type": "status", "data": "ok", "action": message["action"]}),
        room=sid,
    )


from app.devices.web import remote_player, disconnect
