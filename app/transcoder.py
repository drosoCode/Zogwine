import os
import signal
import json
import re
from subprocess import Popen

from .log import logger
from .files import getFileInfos, getMediaPath


class transcoder:
    def __init__(
        self,
        mediaType: int,
        mediaData: int,
        outDir: str = "./",
        encoder: str = "h264_nvenc",
        crf: int = 23,
    ):
        self._file = getMediaPath(mediaType, mediaData)
        self._fileInfos = getFileInfos(mediaType, mediaData)
        self._audioStream = "0"
        self._subStream = "-1"
        self._subFile = ""
        self._enableHLS = True
        self._startFrom = 0
        self._hlsTime = 60
        self._resize = -1
        self._encoder = encoder
        self._crf = crf
        self._outDir = outDir
        self._outFile = outDir.encode("utf-8") + b"/stream"
        self._remove3D = 0
        self._runningProcess = None

    def setAudioStream(self, audioStream: str):
        self._audioStream = str(audioStream)

    def setSub(self, subStream: str, subFile=""):
        self._subStream = str(subStream)

    def enableHLS(self, en, time=-1):
        self._enableHLS = en
        self._hlsTime = time

    def setStartTime(self, time):
        self._startFrom = time

    def setOutputFile(self, outFile: bytes):
        self.__outFile = outFile

    def getOutputFile(self) -> bytes:
        if self._enableHLS:
            return self._outFile + b".m3u8"
        else:
            return (
                self._outFile
                + b"."
                + self._fileInfos["general"]["extension"].encode("utf-8")
            )

    def resize(self, size):
        self._resize = size

    def remove3D(self, stereoType: int):
        # stereoType is 1 for SBS (side by side) or 2 for TAB (top and bottom)
        self._remove3D = stereoType

    def getWatchedDuration(self, data):
        return float(data) + float(self._startFrom)

    def configure(self, args: dict):
        if "audioStream" in args:
            self.setAudioStream(args.get("audioStream"))
        if "subStream" in args:
            self.setSub(args.get("subStream"))
        if "startFrom" in args:
            self.setStartTime(args.get("startFrom"))
        if "resize" in args:
            self.resize(args.get("resize"))
        if "remove3D" in args:
            r3 = args["remove3D"]
            self.remove3D(int(r3))

    def start(self) -> dict:
        if not os.path.exists(self._outDir):
            os.makedirs(self._outDir)

        filePath = self._file
        if int(self._startFrom) > 0:
            ext = filePath[filePath.rfind(".") + 1 :]
            filePath = self._outDir + "/temp." + ext

            cutCmd = (
                b"ffmpeg -y -hide_banner -loglevel fatal -ss "
                + str(self._startFrom).encode("utf-8")
                + b' -i "'
                + self._file.encode("utf-8")
                + b'" -c copy -map 0 '
                + filePath.encode("utf-8")
            )
            logger.info(b"Cutting file with ffmpeg:" + cutCmd)
            os.system(cutCmd)

        cmd = (
            b'ffmpeg -hide_banner -loglevel fatal -i "'
            + filePath.encode("utf-8")
            + b'"'
        )
        cmd += b" -pix_fmt yuv420p -preset medium"

        rm3d = b""
        rm3dMeta = b""
        if self._remove3D == 1:
            rm3d = b"stereo3d=sbsl:ml[v1];[v1]"
            rm3dMeta = b' -metadata:s:v:0 stereo_mode="mono"'
        elif self._remove3D == 2:
            rm3d = b"stereo3d=abl:ml[v1];[v1]"
            rm3dMeta = b' -metadata:s:v:0 stereo_mode="mono"'

        resize = b""
        if int(self._resize) > 0:
            resize = b"[v2];[v2]scale=" + str(self._resize).encode("utf-8") + b":-1"

        if self._subStream != "-1":
            if self._subFile == "":
                if self._fileInfos["subtitles"][int(self._subStream)]["codec"] in [
                    "hdmv_pgs_subtitle",
                    "dvd_subtitle",
                ]:
                    cmd += (
                        b' -filter_complex "[0:v]'
                        + rm3d
                        + b"[0:s:"
                        + self._subStream.encode("utf-8")
                        + b"]overlay"
                        + resize
                        + b'"'
                    )
                else:
                    cmd += (
                        b' -filter_complex "[0:v:0]'
                        + rm3d
                        + b"subtitles='"
                        + filePath.encode("utf-8")
                        + b"':si="
                        + self._subStream.encode("utf-8")
                        + resize
                        + b'"'
                    )
            else:
                cmd += (
                    b' -filter_complex "[0:v:0]'
                    + rm3d
                    + b"subtitles='"
                    + self._subFile
                    + b"':si="
                    + self._subStream.encode("utf-8")
                    + resize
                    + b'"'
                )
        elif self._remove3D:
            if self._remove3D == 1:
                cmd += b' -filter_complex "[0:v:0]stereo3d=sbsl:ml"'
            elif self._remove3D == 2:
                cmd += b' -filter_complex "[0:v:0]stereo3d=abl:ml"'

        if self._remove3D:
            if "ratio" in self._fileInfos:
                cmd += b" -aspect " + self._fileInfos.get("ratio").encode("utf-8")
            else:
                cmd += b" -aspect 16:9"

        if self._audioStream != "0":
            cmd += b" -map 0:a:" + self._audioStream.encode("utf-8")
        cmd += b" -c:a aac -ar 48000 -b:a 128k -ac 2"
        cmd += rm3dMeta
        cmd += b" -c:v " + self._encoder.encode("utf-8")
        cmd += b" -crf " + str(self._crf).encode("utf-8")

        if self._enableHLS:
            cmd += (
                b" -hls_time "
                + str(self._hlsTime).encode("utf-8")
                + b" -hls_playlist_type event -hls_segment_filename "
                + self._outFile
                + b"%03d.ts "
                + self._outFile
                + b".m3u8"
            )
        else:
            cmd += b" " + self._outFile + b"." + self._fileInfos["general"]["extension"]

        logger.info(b"Starting ffmpeg with:" + cmd)
        process = Popen(b"exec " + cmd, shell=True)

        return {"pid": process.pid, "outDir": self._outDir}

    @staticmethod
    def stop(data: dict):
        if "pid" in data:
            os.kill(data["pid"], signal.SIGTERM)
        if "outDir" in data:
            os.system('rm -rf "' + data["outDir"] + '"')
