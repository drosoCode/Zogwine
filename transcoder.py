import os
import json
import re
from subprocess import Popen
from log import logger

class transcoder:

    def __init__(self, filePath, outDir="./", encoder="h264_nvenc", crf=23):
        self._file = None
        self._fileInfos = None
        self._audioStream = 0
        self._subStream = -1
        self._subFile = ""
        self._enableHLS = True
        self._startFrom = 0
        self._hlsTime = 60
        self._resize = -1
        self._encoder = encoder
        self._crf = crf
        self._outDir = outDir
        self._outFile = outDir + "/stream"
        self._remove3D = None
        self._runningProcess = None
        self._file = filePath
        self._fileInfos = self.ffprobe()

    def setAudioStream(self, audioStream):
        self._audioStream = audioStream

    def setSub(self, subStream, subFile=""):
        self._subStream = subStream

    def enableHLS(self, en, time=-1):
        self._enableHLS = en
        self._hlsTime = time

    def setStartTime(self, time):
        self._startFrom = time
        self._fileInfos['general']['startFrom'] = time
    
    def setOutputFile(self, outFile):
        self.__outFile = outFile

    def getOutputFile(self):
        if self._enableHLS:
            return self._outFile+'.m3u8'
        else:
            return self._outFile+'.'+self._fileInfos['general']['extension']

    def resize(self, size):
        self._resize = size

    def remove3D(self, ttype):
        #ttype is SBS (side by side) or TAB (top and bottom)
        self._remove3D = ttype.upper()

    def getFileInfos(self):
        return self._fileInfos

    def getWatchedDuration(self, data):
        if self._enableHLS:
            #data is the name of latest watched hls segment
            name = self._outFile
            pos = self._outFile.rfind("/")
            if pos > 0:
                name = name[pos+1:]
            num = int(re.findall("(?i)(?:"+name+")(\\d+)(?:\\.ts)", data)[0]) + 1
            return num * int(self._hlsTime) + int(self._startFrom)
        else:
            #data is the last timecode
            return int(data) + int(self._startFrom)

    def ffprobe(self):
        cmd = "ffprobe -v quiet -print_format json -show_format -show_streams \""+self._file+"\" > out/data.json"
        logger.debug('FFprobe: '+cmd)
        os.system(cmd)

        with open("out/data.json","r", encoding='utf-8') as f:
            dat = json.load(f, encoding='UTF8')

        data = {
            "general":{
                "format": dat["format"]["format_name"],
                "duration": dat["format"]["duration"],
                "extension": self._file[self._file.rfind('.')+1:],
                "startFrom": 0
            },
            "audio":[],
            "subtitles":[]
        }

        i = 0
        for stream in dat["streams"]:
            lang = ''
            if stream["codec_type"] == "video":
                data["general"]["video_codec"] = stream["codec_name"]
            elif stream["codec_type"] == "audio":
                if 'tags' in stream and 'language' in stream["tags"]:
                    lang = stream["tags"]["language"]
                data["audio"].append({"index":stream["index"], "codec":stream["codec_name"], "channels":stream["channels"], "language": lang})
            elif stream["codec_type"] == "subtitle":
                t = 'SUB'+str(i)
                if 'tags' in stream:
                    if 'title' in stream["tags"]:
                        t = stream["tags"]["title"]
                    if 'language' in stream["tags"]:
                        lang = stream["tags"]["language"]
                data["subtitles"].append({"index":stream["index"], "codec":stream["codec_name"], "language": lang, "title": t})
                i += 1

        return data

    def start(self):
        if not os.path.exists(self._outDir):
            os.makedirs(self._outDir)

        filePath = self._file
        if int(self._startFrom) > 0:
            ext = filePath[filePath.rfind('.')+1:]
            filePath = self._outDir+"/temp."+ext

            cutCmd = "ffmpeg -hide_banner -loglevel error -ss "+str(self._startFrom)+" -i \""+self._file+"\" -c copy -map 0 "+filePath
            logger.info("Cutting file with ffmpeg:"+cutCmd)
            os.system(cutCmd)

        cmd = "ffmpeg -hide_banner -loglevel error -i \""+filePath+"\""
        cmd += " -pix_fmt yuv420p -preset medium"

        rm3d = ""
        rm3dMeta = ""
        if self._remove3D == "SBS":
            rm3d = "stereo3d=sbsl:ml[v1];[v1]"
            rm3dMeta = " -metadata:s:v:0 stereo_mode=\"mono\""
        elif self._remove3D == "TAB":
            rm3d = "stereo3d=tbr:ml[v1];[v1]"
            rm3dMeta = " -metadata:s:v:0 stereo_mode=\"mono\""
        
        resize = ""
        if int(self._resize) > 0:
            resize = "[v2];[v2]scale="+str(self._resize)+":-1"


        if self._subStream != -1:
            if self._subFile == "":
                if self._fileInfos['subtitles'][int(self._subStream)]["codec"] in ["hdmv_pgs_subtitle", "dvd_subtitle"]:
                    cmd += " -filter_complex \"[0:v]"+rm3d+"[0:s:" + self._subStream + "]overlay"+resize+"\""
                else:
                    cmd += " -filter_complex \"[0:v:0]"+rm3d+"subtitles='"+ filePath +"':si="+ self._subStream +resize+"\""
            else:
                cmd += " -filter_complex \"[0:v:0]"+rm3d+"subtitles='"+ self._subFile +"':si="+ self._subStream +resize+"\""


        cmd += " -map 0:a:" + self._audioStream + " -c:a aac -ar 48000 -b:a 128k"
        cmd += rm3dMeta
        cmd += " -c:v " + self._encoder
        cmd += " -crf " + str(self._crf)

        if self._enableHLS:
            cmd += " -hls_time "+str(self._hlsTime)+" -hls_playlist_type event -hls_segment_filename " + self._outFile + "%03d.ts " + self._outFile + ".m3u8"
        else:
            cmd += " "+self._outFile+'.'+self._fileInfos['general']['extension']

    
        logger.info("Starting ffmpeg with:"+cmd)
        self._runningProcess = Popen("exec "+cmd, shell=True)

    def stop(self):
        if self._runningProcess is not None:
            self._runningProcess.kill()
            self._runningProcess = None
            os.system("rm -rf \""+self._outDir+"\"")
