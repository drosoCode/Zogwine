from flask import request, Blueprint, jsonify
import redis
import json
import hashlib
import secrets

from transcoder import transcoder
from log import logger, getLogs
from utils import checkArgs
from dbHelper import sql
from indexer import scanner


user = Blueprint("user", __name__)
allowedMethods = ["GET", "POST"]
sqlConnectionData = {}
r_userTokens = redis.Redis
r_userFiles = redis.Redis
configData = {}


def user_configure(conf):
    global allowedMethods, sqlConnectionData, r_userTokens, r_userFiles, configData
    configData = conf
    sqlConnectionData = {
        "host": configData["db"]["host"],
        "user": configData["db"]["user"],
        "password": configData["db"]["password"],
        "database": configData["db"]["name"],
        "use_unicode": True,
        "charset": "utf8",
    }
    r_userFiles = redis.Redis(
        host=configData["redis"]["host"],
        port=configData["redis"]["port"],
        db=configData["redis"]["filesDB"],
    )
    r_userTokens = redis.Redis(
        host=configData["redis"]["host"],
        port=configData["redis"]["port"],
        db=configData["redis"]["usersDB"],
    )

    @user.route("/api/users/authenticate", methods=["GET", "POST"])
    def authenticateUser():
        sqlConnection = sql(**sqlConnectionData)
        checkArgs(["user", "password"])
        user = request.args["user"]
        password = hashlib.sha256(bytes(request.args["password"], "utf-8")).hexdigest()
        cursor = sqlConnection.cursor(dictionary=True)
        if user != "" and password != "":
            r = (
                "SELECT idUser FROM users WHERE user = '"
                + str(user)
                + "' AND password = '"
                + str(password)
                + "';"
            )
            cursor.execute(r)
            dat = cursor.fetchone()
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
        sqlConnection = sql(**sqlConnectionData)
        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute(
            "SELECT name, admin, cast, kodiLinkBase FROM users WHERE idUser = %(idUser)s",
            {"idUser": r_userTokens.get(token).decode("utf-8")},
        )
        return cursor.fetchone()

    def generateToken(userID):
        t = secrets.token_hex(20)
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