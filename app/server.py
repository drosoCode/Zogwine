#!/usr/bin/python3
import _bootlocale

_bootlocale.getpreferredencoding = lambda *args: "UTF-8"


from flask import request, abort, Flask
import json
import redis

from .log import logger
from .tvs import tvs
from .movie import movie
from .user import user
from .core import core
from .player import player
from .device import device
from .dbHelper import r_runningThreads, r_userTokens
from .utils import getUID, checkUser

"""
DB:
    mediaType: 1=tv_show ep
               2=tv_show
               3=movie
               4=url (youtube, twitch, direct video ...)
"""

r_runningThreads.set("tvs", 0)
r_runningThreads.set("movies", 0)
r_runningThreads.set("upEpisodes", 0)
r_runningThreads.set("cache", 0)
r_runningThreads.set("people", 0)

app = Flask(__name__, static_url_path="")

app.register_blueprint(tvs, url_prefix="/api/tvs")
app.register_blueprint(movie, url_prefix="/api/movie")
app.register_blueprint(user, url_prefix="/api/user")
app.register_blueprint(core)
app.register_blueprint(player)
app.register_blueprint(device)

logger.info("Server Started Successfully")


@app.before_request
def before_request():
    if (
        request.endpoint
        not in [
            "user.signin",
            "user.nginx",
            "core.getImage",
        ]
        and getUID() is None
    ):
        if request.method == "OPTIONS":
            return "ok"
        else:
            abort(401)

    service = request.endpoint[0 : request.endpoint.find(".")]
    if service == "tvs" and not checkUser("allowTvs"):
        abort(403)
    if service == "movies" and not checkUser("allowMovie"):
        abort(403)


@app.route("/", methods=["GET"])
def home():
    return "Zogwine API"
