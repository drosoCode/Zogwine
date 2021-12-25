from flask import request, abort, Response
import os
import mimetypes
import re
import requests
from base64 import b64decode, b64encode
from urllib.parse import urlparse, parse_qs, unquote
import secrets
import hashlib
from decimal import Decimal

from .dbHelper import getSqlConnection, configData, r_userTokens
from .log import logger


def checkArgs(args, data=None):
    for a in args:
        if data is not None:
            if a not in data:
                abort(400)
                return False
        else:
            if a not in request.args:
                abort(400)
                return False
    return True


def checkUser(prop, abrt=True, uid=None):
    sqlConnection, cursor = getSqlConnection()
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, admin, cast, receive, indexof, allowMovie, allowTvs FROM users WHERE idUser = %(idUser)s",
        {"idUser": uid or getUID()},
    )
    d = cursor.fetchone()
    sqlConnection.close()

    props = ["admin", "indexof", "cast", "receive", "allowMovie", "allowTvs"]

    if prop in props and prop in d and d[prop]:
        return True
    elif abrt:
        abort(403)
    else:
        return False


def addCache(data):
    file = os.path.join(configData["config"]["outDir"], "cache", data)
    if not os.path.exists(file):
        with open(file, "wb") as f:
            logger.debug("Adding " + file + " to cache")
            f.write(requests.get(b64decode(data).decode()).content)


def generateToken(userID):
    t = secrets.token_hex(20)
    r_userTokens.set(str(t), str(userID))
    return t


def getUID(token=None) -> int:
    if token is not None:
        d = r_userTokens.get(token)
        if d is not None:
            return int(d.decode("utf-8"))

    if "token" in request.args:
        d = r_userTokens.get(request.args["token"])
        if d is not None:
            return int(d.decode("utf-8"))

    if "Authorization" in request.headers:
        d = r_userTokens.get(request.headers["Authorization"][7:])
        if d is not None:
            return int(d.decode("utf-8"))

    if "X-Original-Uri" in request.headers:
        parsedUrl = urlparse(request.headers["X-Original-Uri"])
        args = parse_qs(parsedUrl.query)
        if "token" in args:
            d = r_userTokens.get(args["token"][0])
            if d is not None:
                return int(d.decode("utf-8"))

    if request.authorization:
        sqlConnection, cursor = getSqlConnection()
        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute(
            "SELECT idUser FROM users WHERE user = %(username)s AND password = %(password)s",
            {
                "username": request.authorization["username"],
                "password": hashlib.sha256(
                    bytes(request.authorization["password"], "utf-8")
                ).hexdigest(),
            },
        )
        d = cursor.fetchone()
        sqlConnection.close()
        if d is not None and "idUser" in d and d["idUser"]:
            return int(d["idUser"])

    return None


def checkAuthorization(mediaType: int, mediaData: str):
    if (mediaType == 1 or mediaType == 2) and checkUser("allowTvs"):
        return True
    elif mediaType == 3 and checkUser("allowMovie"):
        return True
    return False


def encodeImg(img):
    if img is not None and img != "":
        return b64encode(img.encode("utf-8", "surrogateescape")).decode()
    else:
        return None


def ping(host) -> bool:
    return os.system("ping -c 1 -W 1 " + host) == 0


def fixTypes(data):
    if type(data) == list:
        for i in range(len(data)):
            data[i] = __convertTypes(data[i])
        return data
    else:
        return __convertTypes(data)


def __convertTypes(data):
    for k in data:
        if type(data[k]) == bytearray:
            data[k] = data[k].decode("utf-8")
        elif type(data[k]) == Decimal:
            data[k] = float(data[k])
        elif type(data[k]) == dict:
            data[k] = __convertTypes(data[k])
        elif type(data[k]) == list:
            data[k] = fixTypes(data[k])
    #        elif type(data[k]) not in [str, int, float]:
    #            print(type(data))
    return data