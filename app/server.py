#!/usr/bin/python3

from flask import request, abort, Flask
from flask_cors import CORS
import json
import redis

from log import logger
from tvs import tvs, tvs_configure
from movie import movie, movie_configure
from user import user, user_configure
from core import core, core_configure
from player import player, player_configure

"""
DB:
    mediaType: 1=tv_show ep
               2=tv_show
               3=movie
"""

with open("../config/config_dev.json") as f:
    configData = json.load(f)
    r_runningThreads = redis.Redis(
        host=configData["redis"]["host"],
        port=configData["redis"]["port"],
        db=configData["redis"]["threadsDB"],
    )
    r_userTokens = redis.Redis(
        host=configData["redis"]["host"],
        port=configData["redis"]["port"],
        db=configData["redis"]["usersDB"],
    )
    logger.info("Server Started Successfully")

r_runningThreads.set("tvs", 0)
r_runningThreads.set("movies", 0)
r_runningThreads.set("upEpisodes", 0)
r_runningThreads.set("cache", 0)
r_runningThreads.set("people", 0)

app = Flask(__name__, static_url_path="")
CORS(app)

tvs_configure(configData)
movie_configure(configData)
user_configure(configData)
core_configure(configData)
player_configure(configData)

app.register_blueprint(tvs)
app.register_blueprint(movie)
app.register_blueprint(user)
app.register_blueprint(core)
app.register_blueprint(player)

app.config["DEBUG"] = True


@app.before_request
def before_request():
    if request.endpoint not in ["user.authenticateUser", "core.getImage",] and (
        "token" not in request.args or not r_userTokens.exists(request.args["token"])
    ):
        abort(401)


@app.route("/", methods=["GET"])
def home():
    return "Zogwine API"
