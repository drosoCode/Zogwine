from flask import request, Blueprint, jsonify
import redis
import json
import hashlib
import jwt
import time

from transcoder import transcoder
from log import logger, getLogs
from utils import checkArgs

from dbHelper import getSqlConnection, r_userFiles, r_userTokens, configData
from indexer import scanner


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
        "SELECT name, admin, cast, kodiLinkBase FROM users WHERE idUser = %(idUser)s",
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
            "data": getUserData(
                r_userTokens.get(request.args["token"]).decode("utf-8")
            ),
        }
    )


def generateToken(userID):
    t = jwt.encode(
        {"creation": time.time(), "idUser": userID}, "zogwine", algorithm="HS512"
    ).decode("utf8")
    r_userTokens.set(str(t), str(userID))
    return t


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
            obj = transcoder.fromJSON(r_userFiles.get(uid))
            obj.stop()
            del obj
            r_userFiles.delete(uid)
    return jsonify({"status": "ok", "data": "ok"})


"""
@user.route("/api/users/data", methods=["GET", "POST"])
def getUserDataFlask():
    return jsonify(getUserData(request.args["token"]))
"""