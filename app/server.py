#!/usr/bin/python3

from flask import request, abort, Flask
from flask_cors import CORS
import json
import redis

from .log import logger
from .tvs import tvs
from .movie import movie
from .user import user
from .core import core
from .player import player
from .dbHelper import r_runningThreads, r_userTokens

"""
DB:
    mediaType: 1=tv_show ep
               2=tv_show
               3=movie
"""

r_runningThreads.set("tvs", 0)
r_runningThreads.set("movies", 0)
r_runningThreads.set("upEpisodes", 0)
r_runningThreads.set("cache", 0)
r_runningThreads.set("people", 0)

app = Flask(__name__, static_url_path="")
CORS(app)

app.register_blueprint(tvs)
app.register_blueprint(movie)
app.register_blueprint(user)
app.register_blueprint(core)
app.register_blueprint(player)

app.config["DEBUG"] = True

logger.info("Server Started Successfully")


@app.before_request
def before_request():
    if request.endpoint not in ["user.signin", "core.getImage",] and (
        "token" not in request.args or not r_userTokens.exists(request.args["token"])
    ):
        abort(401)


@app.route("/", methods=["GET"])
def home():
    return "Zogwine API"
