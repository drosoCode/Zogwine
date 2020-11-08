from flask import request, abort, Response
import os
import mimetypes
import re
import requests
from base64 import b64decode

from dbHelper import getSqlConnection
from log import logger


def checkArgs(args):
    for a in args:
        if a not in request.args:
            abort(404)
            return False
    return True


def checkUser(uid, prop):
    if prop == "admin":
        sqlConnection, cursor = getSqlConnection()
        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute(
            "SELECT name, icon, admin, kodiLinkBase FROM users WHERE idUser = %(idUser)s",
            {"idUser": uid},
        )
        d = cursor.fetchone()
        sqlConnection.close()
        if "admin" in d and d["admin"]:
            return True
        else:
            abort(403)


def getMediaPath(token, mediaType, mediaData):
    from tvs import tvs_getEpPath
    from movie import mov_getPath

    if mediaType == "1":
        # tvs episode
        return tvs_getEpPath(mediaData)
    elif mediaType == "3":
        # movie
        return mov_getPath(mediaData)
    else:
        return None


def addCache(data):
    file = "../out/cache/" + data
    if not os.path.exists(file):
        with open(file, "wb") as f:
            logger.debug("Adding " + file + " to cache")
            f.write(requests.get(b64decode(data).decode()).content)


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


def getFile(path, requiredMime):
    mime = mimetypes.guess_type(path, strict=False)[0]
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
        resp.headers.add(
            "Content-Disposition", "attachment", filename=path[path.rfind("/") + 1 :]
        )
        return resp
    else:
        abort(404)