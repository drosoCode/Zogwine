from flask import request, Blueprint, jsonify
import redis
import json
import hashlib
from flask_jwt_extended import create_access_token

from transcoder import transcoder
from log import logger, getLogs
from utils import checkArgs

from dbHelper import getSqlConnection, r_userFiles, r_userTokens, configData
from indexer import scanner


user = Blueprint("user", __name__)
allowedMethods = ["GET", "POST"]


@user.route("/api/users/authenticate", methods=["GET", "POST"])
def authenticateUser():
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
            return jsonify({"response": generateToken(dat["idUser"])})
        else:
            logger.warning("Bad Authentication for user: " + str(user))
            return jsonify({"response": "error"})
    else:
        logger.warning("Empty User or Password for authentication")
        return jsonify({"response": "error"})


def getUserData(token):
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT name, admin, cast, kodiLinkBase FROM users WHERE idUser = %(idUser)s",
        {"idUser": r_userTokens.get(token).decode("utf-8")},
    )
    res = cursor.fetchone()
    sqlConnection.close()
    return res


def generateToken(userID):
    t = create_access_token(identity=userID)
    r_userTokens.set(str(t), str(userID))
    return t


def removeToken(token):
    uid = r_userTokens.get(token)
    r_userTokens.delete(token)
    if sum(r_userTokens.get(u) == uid for u in r_userTokens.scan_iter()) == 0:
        if r_userFiles.exists(uid):
            obj = transcoder.fromJSON(r_userFiles.get(uid))
            obj.stop()
            del obj
            r_userFiles.delete(uid)


@user.route("/api/users/data", methods=["GET", "POST"])
def getUserDataFlask():
    return jsonify(getUserData(request.args["token"]))