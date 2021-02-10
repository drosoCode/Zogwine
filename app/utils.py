from flask import request, abort, Response
import os
import mimetypes
import re
import requests
from base64 import b64decode, b64encode
from urllib.parse import urlparse, parse_qs, unquote
import secrets
import hashlib

from .dbHelper import getSqlConnection, configData, r_userTokens
from .log import logger


def checkArgs(args, data=None):
    for a in args:
        if data is not None:
            if a not in data:
                abort(404)
                return False
        else:
            if a not in request.args:
                abort(404)
                return False
    return True


def checkUser(prop, abrt=True):
    sqlConnection, cursor = getSqlConnection()
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute(
        "SELECT name, admin, cast, indexof, allowMovie, allowTvs FROM users WHERE idUser = %(idUser)s",
        {"idUser": getUID()},
    )
    d = cursor.fetchone()
    sqlConnection.close()

    props = ["admin", "indexof", "cast", "allowMovie", "allowTvs"]

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


def getUID() -> int:
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


def get_chunk(full_path, byte1=None, byte2=None):
    file_size = os.stat(full_path).st_size
    start = 0
    length = 102400

    if byte1 < file_size:
        start = byte1
    if byte2:
        length = byte2 + 1 - byte1
    else:
        length = file_size - start

    with open(full_path, "rb") as f:
        f.seek(start)
        chunk = f.read(length)
    return chunk, start, length, file_size


def getFile(path: bytes, requiredMime: str):
    mime = mimetypes.guess_type(path.decode("utf-8"), strict=False)[0]
    if requiredMime in mime:
        range_header = request.headers.get("Range", None)
        byte1, byte2 = 0, None
        if range_header:
            match = re.search(r"(\d+)-(\d*)", range_header)
            groups = match.groups()

            if groups[0]:
                byte1 = int(groups[0])
            if groups[1]:
                byte2 = int(groups[1])

        chunk, start, length, file_size = get_chunk(path, byte1, byte2)
        resp = Response(
            chunk, 206, mimetype=mime, content_type=mime, direct_passthrough=True
        )
        resp.headers.add(
            "Content-Range",
            "bytes {0}-{1}/{2}".format(start, start + length - 1, file_size),
        )
        resp.headers.add("Accept-Ranges", "bytes")
        name = path.decode("utf-8")
        name = name[name.rfind("/") + 1 :]
        resp.headers.add("Content-Disposition", "attachment", filename=name)
        return resp
    else:
        abort(404)