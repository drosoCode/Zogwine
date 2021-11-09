import subprocess
import json
import re
import os
import base64

from .dbHelper import getSqlConnection, configData, r_userFiles
from .urlResolver import getInfos
from .utils import getUID
from .exceptions import InvalidLibraryException


def _getSubtitleFilesList(filePath: bytes) -> list:
    filePath = filePath.decode("utf-8")
    subFiles = []
    path = filePath[: filePath.rfind("/")]
    fileName = filePath[filePath.rfind("/") + 1 : filePath.rfind(".")]
    fileNameLen = len(fileName)
    for p in os.listdir(path):
        if p.find(fileName) == 0 and len(p[fileNameLen : p.rfind(".")]) > 0:
            subFiles.append(
                {
                    "file": base64.b64encode(p[fileNameLen:].encode("utf-8")).decode(
                        "utf-8"
                    ),
                    "title": "subfile",
                    "language": p[fileNameLen : p.rfind(".")],
                    "codec": p[p.rfind(".") + 1 :],
                }
            )
    return subFiles


def getSubPathFromName(filePath: bytes, subFile: bytes) -> bytes:
    filePath = filePath.decode("utf-8")
    return filePath[: filePath.rfind(".")].encode("utf-8") + base64.b64decode(subFile)


def _getFileInfos(path: bytes) -> dict:
    fileName = path.decode("utf-8")[path.decode("utf-8").rindex("/") + 1 :].lower()

    stereo3d = 0
    if re.search("[. -_]?tab[. -_]?", fileName):
        stereo3d = 2
    elif re.search("([. -_]?3d[. -_]?)|([. -_]?sbs[. -_]?)", fileName):
        stereo3d = 1

    cmd = (
        b'ffprobe -v quiet -print_format json -show_format -show_streams "'
        + path
        + b'"'
    )
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        shell=True,
    )
    dat = json.loads(proc.communicate()[0].decode("utf-8"))

    data = {
        "extension": fileName[fileName.rfind(".") + 1 :],
        "stereo3d": stereo3d,
        "audio": [],
        "subtitles": [],
    }

    if "format" not in dat:
        data["format"] = ""
        data["duration"] = -1
        data["size"] = -1
    else:
        data["format"] = dat["format"]["format_name"]
        data["duration"] = dat["format"]["duration"]
        data["size"] = dat["format"]["size"]

    i = 0
    if "streams" in dat:
        for stream in dat["streams"]:
            lang = ""
            if stream["codec_type"] == "video":
                data["video_codec"] = stream.get("codec_name")
                data["pix_fmt"] = stream.get("pix_fmt")
                data["ratio"] = stream.get("display_aspect_ratio")
                data["dimension"] = (
                    str(stream.get("width")) + "x" + str(stream.get("height"))
                )

            elif stream["codec_type"] == "audio":
                if "tags" in stream and "language" in stream["tags"]:
                    lang = stream["tags"]["language"]
                data["audio"].append(
                    {
                        "index": stream["index"],
                        "codec": stream["codec_name"],
                        "channels": stream["channels"],
                        "language": lang,
                    }
                )

            elif stream["codec_type"] == "subtitle":
                t = "SUB" + str(i)
                if "tags" in stream:
                    if "title" in stream["tags"]:
                        t = stream["tags"]["title"]
                    if "language" in stream["tags"]:
                        lang = stream["tags"]["language"]
                data["subtitles"].append(
                    {
                        "index": stream["index"],
                        "codec": stream["codec_name"],
                        "language": lang,
                        "title": t,
                    }
                )
                i += 1
    else:
        data["video_codec"] = ""
        data["pix_fmt"] = ""
        data["ratio"] = ""
        data["dimension"] = ""

    return data


def addFile(file: str, idLib: int) -> int:

    fullPath = os.path.join(
        getLibPath(idLib),
        file,
    ).encode("utf-8")

    infos = _getFileInfos(fullPath)
    infos.update({"idLib": idLib, "path": file})
    infos.update({"subtitles": json.dumps(infos["subtitles"])})
    infos.update({"audio": json.dumps(infos["audio"])})

    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "INSERT INTO video_files (idLib, path, format, duration, extension, audio, subtitles, stereo3d, ratio, dimension, pix_fmt, video_codec, size) VALUES (%(idLib)s, %(path)s, %(format)s, %(duration)s, %(extension)s, %(audio)s, %(subtitles)s, %(stereo3d)s, %(ratio)s, %(dimension)s, %(pix_fmt)s, %(video_codec)s, %(size)s)",
        infos,
    )
    sqlConnection.commit()
    cursor.execute(
        "SELECT idVid FROM video_files WHERE path = %(path)s;", {"path": file}
    )
    dat = cursor.fetchone()
    sqlConnection.close()
    return int(dat["idVid"])


def updateFile(idVid: int, file: str = None, idLib: int = None):
    sqlConnection, cursor = getSqlConnection()

    if file is None or idLib is None:
        cursor.execute(
            "SELECT idLib, path FROM video_files WHERE idVid = %(idVid)s;",
            {"idVid": idVid},
        )
        d = cursor.fetchone()
        idLib = d["idLib"]
        file = d["path"]

    fullPath = os.path.join(
        getLibPath(idLib),
        file,
    ).encode("utf-8")
    infos = _getFileInfos(fullPath)
    infos.update({"idLib": idLib, "path": file})
    infos.update({"subtitles": json.dumps(infos["subtitles"])})
    infos.update({"audio": json.dumps(infos["audio"])})
    infos.update({"idVid": idVid})

    cursor.execute(
        "UPDATE video_files SET idLib = %(idLib)s, path = %(path)s, format = %(format)s, duration = %(duration)s, extension = %(extension)s, audio = %(audio)s, subtitles = %(subtitles)s, stereo3d = %(stereo3d)s, ratio = %(ratio)s, dimension = %(dimension)s, pix_fmt = %(pix_fmt)s, video_codec = %(video_codec)s, size = %(size)s WHERE idVid = %(idVid)s",
        infos,
    )
    sqlConnection.commit()
    sqlConnection.close()


def getMediaPath(mediaType: int, mediaData: str, addBasePath: bool = True) -> bytes:
    sqlConnection, cursor = getSqlConnection()
    base = ""
    if addBasePath:
        base = configData["config"]["contentPath"]

    if mediaType == 1:
        cursor.execute(
            "SELECT l.path AS lib, v.path AS path FROM video_files v INNER JOIN episodes e ON (e.idVid = v.idVid) INNER JOIN tv_shows t ON (e.idShow = t.idShow) INNER JOIN libraries l ON (t.idLib = l.id) WHERE idEpisode = %(mediaData)s;",
            {"mediaData": mediaData},
        )
        dat = cursor.fetchone()
        sqlConnection.close()
        return os.path.join(base, dat["lib"], dat["path"]).encode("utf-8")
    if mediaType == 2:
        cursor.execute(
            "SELECT l.path AS lib, t.path AS path FROM tv_shows t INNER JOIN libraries l ON (t.idLib = l.id) WHERE idShow = %(mediaData)s",
            {"mediaData": mediaData},
        )
        dat = cursor.fetchone()
        sqlConnection.close()
        return os.path.join(base, dat["lib"], dat["path"]).encode("utf-8")
    elif mediaType == 3:
        cursor.execute(
            "SELECT l.path AS lib, v.path AS path FROM video_files v INNER JOIN movies m ON (m.idVid = v.idVid) INNER JOIN libraries l ON (v.idLib = l.id) WHERE idMovie = %(mediaData)s;",
            {"mediaData": mediaData},
        )
        dat = cursor.fetchone()
        sqlConnection.close()
        return os.path.join(base, dat["lib"], dat["path"]).encode("utf-8")
    else:
        sqlConnection.close()
        return None


def getFileInfos(mediaType: int, mediaData: int) -> dict:
    sqlConnection, cursor = getSqlConnection()
    dat = {}
    if mediaType == 1:
        cursor.execute(
            "SELECT format, duration, extension, audio, subtitles, stereo3d, ratio, dimension, pix_fmt, video_codec, size FROM video_files v INNER JOIN episodes e ON (e.idVid = v.idVid) WHERE idEpisode = %(mediaData)s;",
            {"mediaData": mediaData},
        )
        dat = cursor.fetchone()
    elif mediaType == 3:
        cursor.execute(
            "SELECT format, duration, extension, audio, subtitles, stereo3d, ratio, dimension, pix_fmt, video_codec, size FROM video_files v INNER JOIN movies m ON (m.idVid = v.idVid) WHERE idMovie = %(mediaData)s;",
            {"mediaData": mediaData},
        )
        dat = cursor.fetchone()
    elif mediaType == 4:
        dat = getInfos(mediaData)

    if "audio" in dat:
        dat["audio"] = json.loads(dat["audio"].encode("utf-8"))

    if "subtitles" in dat:
        dat["subtitles"] = json.loads(dat["subtitles"].encode("utf-8"))
    else:
        dat["subtitles"] = []

    dat["subtitles"] += _getSubtitleFilesList(getMediaPath(mediaType, mediaData))

    sqlConnection.close()
    return dat


def getOutputDir(uid: int = None):
    if uid is None:
        uid = getUID()
    return os.path.join(configData["config"]["outDir"], str(uid))


def getMediaFromUrl(url: str) -> dict:
    pos = url.find("/out/")
    if pos != -1:
        pos += 5
        uid = url[pos : url.find("/", pos + 1)]
        data = r_userFiles.get(uid)
        if data is not None:
            data = json.loads(data)
            return {
                "mediaType": int(data["mediaType"]),
                "mediaData": str(data["mediaData"]),
            }
        else:
            return None
    else:
        pos = url.find("content/")
        if pos == -1:
            return None
        pos += 8
        sqlConnection, cursor = getSqlConnection()
        if url[pos:].find(configData["config"]["moviePath"]) == 0:
            # movie
            cursor.execute(
                "SELECT idMovie FROM movies m JOIN video_files v ON (v.idVid = m.idVid) WHERE path = %(path)s;",
                {"path": url[pos + len(configData["config"]["moviePath"]) + 1 :]},
            )
            dat = cursor.fetchone()["idMovie"]
            sqlConnection.close()
            return {"mediaType": 3, "mediaData": dat}

        elif url[pos:].find(configData["config"]["tvsPath"]) == 0:
            # tvs
            cursor.execute(
                "SELECT idEpisode FROM episodes e JOIN video_files v ON (v.idVid = e.idVid) WHERE path = %(path)s;",
                {"path": url[pos + len(configData["config"]["tvsPath"]) + 1 :]},
            )
            dat = cursor.fetchone()["idEpisode"]
            sqlConnection.close()
            return {"mediaType": 1, "mediaData": str(dat)}


def getLibPath(idLib: int) -> str:
    """
    returns the absolute path to the root folder of a library
    Args:
        idLib: the library id
    """
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT path FROM libraries WHERE id = %(id)s;",
        {"id": idLib},
    )
    data = cursor.fetchone()
    sqlConnection.close()
    if data is not None and data.get("path") is not None:
        return os.path.join(
            configData["config"]["contentPath"],
            data["path"],
        )
    else:
        raise InvalidLibraryException(f"library not found for id {idLib}")