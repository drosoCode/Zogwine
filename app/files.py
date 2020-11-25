import subprocess
import json
import re

from .dbHelper import getSqlConnection, configData
from .urlResolver import getInfos


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
        filePath = configData["config"]["tvsDirectory"].encode() + b"/" + file
    elif mediaType == 3:
        filePath = configData["config"]["moviesDirectory"].encode() + b"/" + file
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


def getMediaPath(mediaType: int, mediaData: int) -> bytes:
    sqlConnection, cursor = getSqlConnection()
    if mediaType == 1:
        cursor.execute(
            u"SELECT path FROM video_files v INNER JOIN episodes e ON (e.idVid = v.idVid) WHERE idEpisode = %(mediaData)s;",
            {u"mediaData": mediaData},
        )
        dat = cursor.fetchone()[u"path"]
        sqlConnection.close()
        return configData[u"config"][u"tvsDirectory"] + "/" + dat
    elif mediaType == 3:
        cursor.execute(
            u"SELECT path FROM video_files v INNER JOIN movies m ON (m.idVid = v.idVid) WHERE idMovie = %(mediaData)s;",
            {"mediaData": mediaData},
        )
        dat = cursor.fetchone()["path"]
        sqlConnection.close()
        return configData["config"]["moviesDirectory"] + "/" + dat
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

    sqlConnection.close()
    return dat