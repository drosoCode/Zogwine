import subprocess
import json
import re
import os
import base64

from .dbHelper import getSqlConnection, configData, r_userFiles
from .urlResolver import getInfos
from .utils import getUID


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
        "extension": fileName[fileName.rfind(u".") + 1 :],
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
            lang = u""
            if stream["codec_type"] == u"video":
                data["video_codec"] = stream.get(u"codec_name")
                data["pix_fmt"] = stream.get(u"pix_fmt")
                data["ratio"] = stream.get(u"display_aspect_ratio")
                data["dimension"] = (
                    str(stream.get(u"width")) + "x" + str(stream.get(u"height"))
                )

            elif stream["codec_type"] == u"audio":
                if u"tags" in stream and u"language" in stream["tags"]:
                    lang = stream["tags"]["language"]
                data["audio"].append(
                    {
                        u"index": stream["index"],
                        u"codec": stream["codec_name"],
                        u"channels": stream["channels"],
                        u"language": lang,
                    }
                )

            elif stream[u"codec_type"] == u"subtitle":
                t = u"SUB" + str(i)
                if u"tags" in stream:
                    if u"title" in stream["tags"]:
                        t = stream["tags"]["title"]
                    if u"language" in stream["tags"]:
                        lang = stream["tags"]["language"]
                data[u"subtitles"].append(
                    {
                        u"index": stream["index"],
                        u"codec": stream["codec_name"],
                        u"language": lang,
                        u"title": t,
                    }
                )
                i += 1
    else:
        data["video_codec"] = ""
        data["pix_fmt"] = ""
        data["ratio"] = ""
        data["dimension"] = ""

    return data


def addFile(file: bytes, mediaType: int) -> int:
    if mediaType == 1:
        filePath = os.path.join(
            configData["config"]["contentPath"].encode(),
            configData["config"]["tvsPath"].encode(),
            file,
        )
    elif mediaType == 3:
        filePath = os.path.join(
            configData["config"]["contentPath"].encode(),
            configData["config"]["moviePath"].encode(),
            file,
        )
    else:
        return -1

    infos = _getFileInfos(filePath)
    infos.update({u"mediaType": mediaType, u"path": file})
    infos.update({u"subtitles": json.dumps(infos[u"subtitles"])})
    infos.update({u"audio": json.dumps(infos[u"audio"])})

    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        u"INSERT INTO video_files (mediaType, path, format, duration, extension, audio, subtitles, stereo3d, ratio, dimension, pix_fmt, video_codec, size) VALUES (%(mediaType)s, %(path)s, %(format)s, %(duration)s, %(extension)s, %(audio)s, %(subtitles)s, %(stereo3d)s, %(ratio)s, %(dimension)s, %(pix_fmt)s, %(video_codec)s, %(size)s)",
        infos,
    )
    sqlConnection.commit()
    cursor.execute(
        u"SELECT idVid FROM video_files WHERE path = %(path)s;", {u"path": file}
    )
    dat = cursor.fetchone()
    sqlConnection.close()
    return int(dat[u"idVid"])


def getMediaPath(mediaType: int, mediaData: str, addBasePath: bool = True) -> bytes:
    sqlConnection, cursor = getSqlConnection()
    base = b""
    if addBasePath:
        base = configData["config"]["contentPath"].encode()

    if mediaType == 1:
        cursor.execute(
            u"SELECT path FROM video_files v INNER JOIN episodes e ON (e.idVid = v.idVid) WHERE idEpisode = %(mediaData)s;",
            {u"mediaData": mediaData},
        )
        dat = cursor.fetchone()[u"path"]
        sqlConnection.close()
        return os.path.join(
            base,
            configData["config"]["tvsPath"].encode(),
            dat.encode("utf-8"),
        )
    elif mediaType == 3:
        cursor.execute(
            u"SELECT path FROM video_files v INNER JOIN movies m ON (m.idVid = v.idVid) WHERE idMovie = %(mediaData)s;",
            {"mediaData": mediaData},
        )
        dat = cursor.fetchone()["path"]
        sqlConnection.close()
        return os.path.join(
            base,
            configData["config"]["moviePath"].encode(),
            dat.encode("utf-8"),
        )
    else:
        return None


def getFileInfos(mediaType: int, mediaData: int) -> dict:
    sqlConnection, cursor = getSqlConnection()
    dat = {}
    if mediaType == 1:
        cursor.execute(
            u"SELECT format, duration, extension, audio, subtitles, stereo3d, ratio, dimension, pix_fmt, video_codec, size FROM video_files v INNER JOIN episodes e ON (e.idVid = v.idVid) WHERE idEpisode = %(mediaData)s;",
            {u"mediaData": mediaData},
        )
        dat = cursor.fetchone()
    elif mediaType == 3:
        cursor.execute(
            u"SELECT format, duration, extension, audio, subtitles, stereo3d, ratio, dimension, pix_fmt, video_codec, size FROM video_files v INNER JOIN movies m ON (m.idVid = v.idVid) WHERE idMovie = %(mediaData)s;",
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
