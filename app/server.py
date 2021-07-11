#!/usr/bin/python3
from gevent import monkey

monkey.patch_all()

import _bootlocale

_bootlocale.getpreferredencoding = lambda *args: "UTF-8"


from flask import request, abort, Flask, send_from_directory, jsonify
import socketio

import yaml

from .log import logger
from .tvs import tvs
from .movie import movie
from .user import user
from .core import core
from .player import player
from .device import device
from .tracker import tracker
from .scraper import scraper
from .dbHelper import r_runningThreads, r_userTokens, configData
from .utils import getUID, checkUser
from .watcher import startWatcher
from .socketio import sio

"""
DB:
    mediaType: 1=tv_show ep
               2=tv_show
               3=movie
               4=url (youtube, twitch, direct video ...)
               5=reserved (tvshow season ?)
               6=reserved (movie collection ?)
"""

startWatcher()

r_runningThreads.set("tvs", 0)
r_runningThreads.set("movies", 0)
r_runningThreads.set("upEpisodes", 0)
r_runningThreads.set("cache", 0)
r_runningThreads.set("people", 0)

app = Flask(__name__, static_url_path="")

app.register_blueprint(tvs, url_prefix="/api/tvs")
app.register_blueprint(movie, url_prefix="/api/movie")
app.register_blueprint(user, url_prefix="/api/user")
app.register_blueprint(core, url_prefix="/api")
app.register_blueprint(player, url_prefix="/api/player")
app.register_blueprint(device, url_prefix="/api/device")
app.register_blueprint(tracker, url_prefix="/api/tracker")
app.register_blueprint(scraper, url_prefix="/api/scraper")

app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

logger.info("Server Started Successfully")


@app.before_request
def before_request():
    if (
        request.endpoint
        not in ["user.signin", "user.nginx", "core.getImage", "swaggerAssets"]
    ) and getUID() is None:
        if request.method == "OPTIONS":
            return "ok"
        else:
            abort(401)

    service = request.endpoint[0 : request.endpoint.find(".")]
    if service == "tvs" and not checkUser("allowTvs"):
        abort(403)
    if service == "movies" and not checkUser("allowMovie"):
        abort(403)


@app.route("/api/", methods=["GET"])
def home():
    return "Zogwine API"


@app.route("/api/swagger/", methods=["GET"])
@app.route("/api/swagger/openapi.<extension>", methods=["GET"])
def swagger(extension=None):
    checkUser("admin")
    if extension == "yaml":
        return send_from_directory(
            "../swagger", "openapi.yaml", mimetype="text/yaml", as_attachment=True
        )
    elif extension == "json":
        with open("swagger/openapi.yaml", "r") as f:
            return jsonify(yaml.full_load(f))
        return abort(404)
    else:
        return send_from_directory("../swagger", "index.html", mimetype="text/html")


@app.route("/api/swagger/assets/<file>", methods=["GET"])
def swaggerAssets(file):
    if file in [
        "swagger-ui-bundle.js",
        "swagger-ui-standalone-preset.js",
        "swagger-ui.css",
    ]:
        return send_from_directory(
            "../swagger/assets",
            file,
            mimetype=("text/css" if file == "swagger-ui.css" else "text/javascript"),
        )
    return abort(404)
