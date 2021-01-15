from flask import request, Blueprint, jsonify
import redis
import json
import hashlib
import time
from urllib.parse import urlparse, parse_qs, unquote

from .transcoder import transcoder
from .log import logger, getLogs
from .utils import checkArgs, getUID, generateToken, checkUser

from .dbHelper import getSqlConnection, r_userFiles, r_userTokens, configData
from .indexer import scanner


user = Blueprint("user", __name__)
allowedMethods = ["GET", "POST"]


@user.route("/api/user/signin", methods=["GET", "POST"])
def signin():
    checkArgs(["user", "password"])
    user = request.args["user"]
    password = hashlib.sha256(bytes(request.args["password"], "utf-8")).hexdigest()
    if user != "" and password != "":
        sqlConnection, cursor = getSqlConnection()
        r = (
            "SELECT idUser FROM users WHERE user = '"
            + str(user)
            + "' AND password = '"
            + str(password)
            + "';"
        )
        cursor.execute(r)
        dat = cursor.fetchone()
        sqlConnection.close()
        if dat != None and "idUser" in dat:
            logger.info("User: " + str(user) + " successfully authenticated")
            return jsonify({"status": "ok", "data": generateToken(dat["idUser"])})
        else:
            logger.warning("Bad Authentication for user: " + str(user))
            return jsonify({"status": "error", "data": "error"})
    else:
        logger.warning("Empty User or Password for authentication")
        return jsonify({"status": "error", "data": "error"})


def getUserData(userID):
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT name, admin, cast, allowMovie, allowTvs FROM users WHERE idUser = %(idUser)s",
        {"idUser": userID},
    )
    res = cursor.fetchone()
    sqlConnection.close()
    return res


@user.route("/api/user/data", methods=["GET", "POST"])
def getUserDataFlask():
    return jsonify(
        {
            "status": "ok",
            "data": getUserData(getUID()),
        }
    )


@user.route("/api/user/signout", methods=["GET", "POST"])
def signout():
    uid = str(r_userTokens.get(request.args["token"]))
    r_userTokens.delete(request.args["token"])
    s = 0
    for u in r_userTokens.scan_iter():
        if r_userTokens.get(str(u)) == uid:
            s += 1

    if s == 0:
        if r_userFiles.exists(uid):
            transcoder.stop(r_userFiles.get(uid))
            r_userFiles.delete(uid)
    return jsonify({"status": "ok", "data": "ok"})


@user.route("/api/user/nginx", methods=["GET", "POST"])
def nginx():
    extensions = [".mkv", ".avi", ".mp4"]

    uid = getUID()
    if uid == None:
        # 401 with authorisation popup
        return (
            "Unauthorized",
            401,
            {"WWW-Authenticate": 'Basic realm="Login Required"'},
        )

    if "X-Original-Uri" not in request.headers or request.remote_addr != "127.0.0.1":
        return ("Unauthorized", 401)

    path = unquote(urlparse(request.headers["X-Original-Uri"]).path)
    path = path[1:]  # strip the initial /

    pos = path.find("/")
    if pos == -1:
        return ("Unauthorized", 401)
    service = path[0:pos]

    if service == "content":
        if checkUser("indexof"):
            return "ok"
        elif path[path.rfind(".") :] in extensions:
            if path[pos + 1 :].find(
                configData["config"]["moviePath"]
            ) == 0 and checkUser("allowMovie"):
                return "ok"

            elif path[pos + 1 :].find(
                configData["config"]["tvsPath"]
            ) == 0 and checkUser("allowTvs"):
                return "ok"

    elif service == "out":
        aPath = "out/" + str(uid) + "/"
        if (
            path[0 : len(aPath)] == aPath
            and "/" not in path[len(aPath) :]
            and path[path.rfind(".") :] == ".ts"
        ):
            return "ok"

    return ("Unauthorized", 401)