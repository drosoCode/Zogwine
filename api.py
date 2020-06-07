import requests
#import mysql.connector as sql
from dbHelper import sql
import json
import os
import time
import base64
import hashlib
import re
from subprocess import Popen
import shutil
import signal
import secrets
from base64 import b64decode

from indexer import scanner
from log import logger

class api:

    def __init__(self, configFile):
        with open(configFile) as f:
            data = json.load(f)
            self._data = data
            self._connection = sql(host=data["db"]["host"],user=data["db"]["user"],password=data["db"]["password"],database='mediaController')
            self._fileDuration = {}
            self._userProcess = {}
            self._userTokens = {}

            self._viewedThreshold = 0.9 #set file as viewed if 90% or more is viewed
        logger.info('API Class Instancied Successfully')

    def getUserData(self,token):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT name, icon, admin, kodiLinkBase FROM users WHERE idUser = '"+str(self._userTokens[token])+"';")
        return cursor.fetchone()

    def authenticateUser(self, user, password):
        password = hashlib.sha256(bytes(password, 'utf-8')).hexdigest()
        cursor = self._connection.cursor(dictionary=True)
        if user != "" and password != "":
            r = "SELECT idUser FROM users WHERE user = '"+str(user)+"' AND password = '"+str(password)+"';"
            cursor.execute(r)
            dat = cursor.fetchone()
            if dat != None and "idUser" in dat:
                logger.info('User: '+str(user)+' successfully authenticated')
                return self.generateToken(dat["idUser"])
            else:
                logger.warning('Bad Authentication for user: '+str(user))
                return False
        else:
            logger.warning('Empty User or Password for authentication')
            return False

    def isAdmin(self, token):
        d = self.getUserData(token)
        if "admin" in d and d["admin"]:
            return True
        else:
            return False

    def generateToken(self, userID):
        vals = self._userTokens.values()
        try:
            i = vals.index(userID)
            del self._userTokens[vals[i]]
        except:
            pass
        t = secrets.token_hex(20)
        self._userTokens[t] = userID
        return t

    def checkToken(self, token):
        return token in self._userTokens

    def getStatistics(self, token):
        avgEpTime = 0.5 #h
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(idView) AS watchedEpCount, SUM(viewCount) AS watchedEpSum FROM tvs_status WHERE viewCount > 0 AND idUser = "+str(self._userTokens[token])+";")
        dat1 = cursor.fetchone()
        cursor.execute("SELECT COUNT(DISTINCT idShow) AS tvsCount, COUNT(idEpisode) AS epCount FROM episodes;")
        dat2 = cursor.fetchone()
        if "watchedEpSum" not in dat1 or dat1["watchedEpSum"] == None:
            dat1["watchedEpSum"] = 0
        return {"watchedEpCount":int(dat1["watchedEpCount"]), "watchedEpSum":int(dat1["watchedEpSum"]), "tvsCount":int(dat2["tvsCount"]), "epCount": int(dat2["epCount"]), "lostTime": avgEpTime * int(dat1["watchedEpSum"])}
    
    def addCache(self, data):
        file = 'out/cache/'+data
        if not os.path.exists(file):
            with open(file, 'wb') as f:
                f.write(requests.get(b64decode(data).decode()).content)

    def refreshCache(self):
        self.tvs_refreshCache()
        self.mov_refreshCache()

    def runScan(self):
        self.tvs_runScan()
        self.mov_runScan()

######################################################################## TVS ##############################################################################

    def tvs_getData(self, token, mr=False):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        mrDat = ''
        if mr:
            mrDat = 'NOT '
        cursor.execute("SELECT idShow AS id, title, overview, CONCAT('/cache/image?id=',icon) AS icon, CONCAT('/cache/image?id=',fanart) AS fanart, rating, premiered, genre, scraperName, scraperID, path, multipleResults, (SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons, (SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes, (SELECT COUNT(v.idView) FROM episodes e LEFT JOIN tvs_status v ON (v.idEpisode = e.idEpisode) WHERE e.idShow = t.idShow AND viewCount > 0  AND idUser = "+str(idUser)+") AS viewedEpisodes, CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND dataType = 'tv_shows'),scraperID) AS scraperLink FROM tv_shows t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;")
        return cursor.fetchall()
    
    def tvs_getEp(self, idShow, token):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT idEpisode AS id, title, overview, CONCAT('/cache/image?id=',icon) AS icon, season, episode, rating, scraperName, scraperID, (SELECT viewCount FROM tvs_status WHERE idEpisode = e.idEpisode AND idUser = "+str(idUser)+") AS viewCount FROM episodes e WHERE idShow = "+str(idShow)+" ORDER BY season, episode;")
        return cursor.fetchall()
    
    def tvs_setID(self, idShow, resultID):
        #the resultID is the one from the json list of multipleResults entry
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT multipleResults FROM tv_shows WHERE idShow = "+str(idShow)+";")
        data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
        cursor.execute("UPDATE tv_shows SET scraperName = %s, scraperID = %s, scraperData = %s, forceUpdate = 1, multipleResults = NULL WHERE idShow = %s;", (data["scraperName"], data["id"], data["scraperData"], idShow))
        self._connection.commit()
        return True

    def tvs_runScan(self):
        scanner(self._connection, 'tvs', self._data["api"]).scanDir(self._data["config"]["tvsDirectory"])
        return True

    def tvs_getFileInfos(self, token, episodeID):
        #get file infos
        epPath = self.tvs_getEpPath(episodeID)
        cmd = "ffprobe -v quiet -print_format json -show_format -show_streams \""+epPath+"\" > out/data.json"

        logger.debug('FFprobe: '+cmd)
        os.system(cmd)

        with open("out/data.json","r", encoding='utf-8') as f:
            dat = json.load(f, encoding='UTF8')

        #get last view end if available
        startFrom = 0
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT viewTime FROM tvs_status WHERE idUser = '"+str(self._userTokens[token])+"' AND idEpisode = '"+str(episodeID)+"';")
        data = cursor.fetchone()
        if data != None and "viewTime" in data:
            if float(data["viewTime"]) > float(dat["format"]["duration"])*self._viewedThreshold:
                startFrom = float(data["viewTime"])

        data = {
            "general":{
                "format": dat["format"]["format_name"],
                "duration": dat["format"]["duration"],
                "extension": epPath[epPath.rfind('.')+1:],
                "startFrom": startFrom
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

        self._fileDuration[episodeID] = [dat["format"]["duration"]]
        return data

    def tvs_getEpPath(self, idEpisode):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT CONCAT(t.path, '/', e.path) AS path FROM tv_shows t INNER JOIN episodes e ON t.idShow = e.idShow WHERE e.idEpisode = "+str(idEpisode)+";")
        path = self._data["config"]["tvsDirectory"]+'/'+cursor.fetchone()['path']
        logger.debug('Getting episode path for id:'+str(idEpisode)+' -> '+path)
        return path

    def tvs_startTranscoder(self, idEpisode, token, audioStream, subStream, subTxt, startFrom=0, resize=0):
        logger.info('Starting transcoder for episode '+str(idEpisode)+' and user '+str(self._userTokens[token]))
        path = self.tvs_getEpPath(idEpisode)

        #remove old data in this dir, if it still exists
        outFile = 'out/'+token
        if os.path.exists(outFile) and ".." not in outFile:
            #shutil.rmtree(outFile)
            os.system("rm -rf "+outFile)

        #recreate an empty out dir
        if not os.path.exists(outFile):
            os.mkdir(outFile)
        outFile += '/stream'

        crf = str(self._data["config"]['crf']) #recommanded: 23
        encoder = str(self._data["config"]['encoder']) #default: h264_nvenc
        hlsTime = str(self._data["config"]['hlsTime']) #in seconds
        
        if int(startFrom) > 0:
            ext = path[path.rfind('.')+1:]
            cutCmd = "ffmpeg -hide_banner -loglevel error -ss "+str(startFrom)+" -i \""+path+"\" -c copy -map 0 out/"+token+"/temp."+ext
            logger.info("Cutting video with ffmpeg:"+cutCmd)
            os.system(cutCmd)
            path = "out/"+token+"/temp."+ext

        size = ""
        if '..' not in path:
            if subStream != "-1":
                if int(resize) > 0:
                    size = "[v];[v]scale="+str(resize)+":-1"

                if subTxt == "1":
                    cmd = "-filter_complex \"[0:v:0]subtitles='"+ path +"':si="+ subStream +size+"\" -map 0:a:"+ audioStream +" -pix_fmt yuv420p -crf " + crf + " -c:v "+ encoder +" -c:a aac -ar 48000 -b:a 128k -hls_time "+hlsTime+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8 "
                else:
                    cmd = "-pix_fmt yuv420p -preset medium -filter_complex \"[0:v][0:s:" + subStream + "]overlay"+size+"\" -map 0:a:" + audioStream + " -c:a aac -ar 48000 -b:a 128k -c:v h264_nvenc -crf " + crf + " -hls_time "+hlsTime+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"
            else:
                if int(resize) > 0:
                    size = "-vf scale="+str(resize)+":-1 "
                cmd = "-pix_fmt yuv420p -c:a aac -ar 48000 -b:a 128k -pix_fmt yuv420p -c:v "+ encoder +" -map 0:a:" + audioStream + " -map 0:v:0 -crf " + crf + " "+size+" -hls_time "+hlsTime+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"

            cmd = "ffmpeg -hide_banner -loglevel error -i \""+ path +"\" " + cmd
            logger.info("Starting ffmpeg with:"+cmd)
            process = Popen("exec "+cmd, shell=True)
            self._userProcess[token] = process

            self._fileDuration[idEpisode].append(startFrom)

            return True
        else:
            return False
    
    def tvs_stopTranscoder(self, token):
        logger.info('Stopping transcoder for user '+str(self._userTokens[token]))
        if token in self._userProcess:
            self._userProcess[token].kill()
            del self._userProcess[token]
            
        if token != "" and ".." not in token:
            #shutil.rmtree('out/'+token)
            os.system("rm -rf \"out/"+token+"\"")
            os.system("rm -rf \"out/"+token+"\"")

    def tvs_setViewedTime(self, idEpisode, token, lastRequestedFile, endTime=-1):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT idView, viewCount FROM tvs_status WHERE idUser = '"+str(self._userTokens[token])+"' AND idEpisode = '"+str(idEpisode)+"';")
        data = cursor.fetchone()
        viewAdd = 0

        
        if lastRequestedFile is not None and idEpisode in self._fileDuration:
            d = float(self._fileDuration[idEpisode][0])

            if endTime == -1 and lastRequestedFile != None:
                #transcoded video
                timeSplit = int(self._data["config"]["hlsTime"])
                num = int(re.findall("(?i)(?:stream)(\\d+)(?:\\.ts)", lastRequestedFile)[0]) + 1
                startFrom = float(self._fileDuration[idEpisode][1])
                endTime = num*timeSplit + startFrom

            if d is not None and endTime > d*self._viewedThreshold:
                viewAdd = 1

            if data != None and "viewCount" in data:
                droso = (str(data["viewCount"]+viewAdd), str(endTime), str(data["idView"]))
                print(droso)
                cursor.execute("UPDATE tvs_status SET viewCount = %s, viewTime = %s WHERE idView = %s;", droso)
            else:
                cursor.execute("INSERT INTO tvs_status (idUser, idEpisode, viewCount, viewTime) VALUES (%s, %s, 1, %s);", (str(self._userTokens[token]), str(idEpisode), str(viewAdd), str(endTime)))

            del self._fileDuration[idEpisode]

            return True

    def tvs_toggleViewed(self, idShow, token, season='all'):
        ids = self.tvs_getEp(idShow, token)
        for i in ids:
            if season == 'all' or int(season) == int(i["season"]):
                self.tvs_toggleViewedEp(i["id"],token)
        return True

    def tvs_toggleViewedEp(self, idEpisode, token):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT viewCount FROM tvs_status WHERE idUser = '"+str(self._userTokens[token])+"' AND idEpisode = '"+str(idEpisode)+"';")
        data = cursor.fetchone()
        count = 0
        if data != None and "viewCount" in data:
            #update
            count = data["viewCount"]
            if count > 0:
                count = 0
            else:
                count = 1
            cursor.execute("UPDATE tvs_status SET viewCount = %s WHERE idUser = %s AND idEpisode = %s;", (str(count), str(self._userTokens[token]), str(idEpisode)))
        else:
            cursor.execute("INSERT INTO tvs_status (idUser, idEpisode, viewCount) VALUES (%s, %s, 1);", (str(self._userTokens[token]), str(idEpisode)))
        self._connection.commit()
        return True
        
    def tvs_refreshCache(self):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT icon, fanart FROM tv_shows;")
        data = cursor.fetchall()
        for d in data:
            if d["icon"] != None:
                self.addCache(d["icon"])
            if d["fanart"] != None:
                self.addCache(d["fanart"])
        cursor.execute("SELECT icon FROM episodes;")
        data = cursor.fetchall()
        for d in data:
            if d["icon"] != None:
                self.addCache(d["icon"])

##################################################### MOVIES #########################################################

    def mov_runScan(self):
        scanner(self._connection, 'movies', self._data["api"]).scanDir(self._data["config"]["moviesDirectory"])
        return True

    def mov_getData(self, token, mr=False):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        mrDat = ''
        if mr:
            mrDat = 'NOT '
        cursor.execute("SELECT idMovie AS id, title, overview, CONCAT('/cache/image?id=',icon) AS icon, CONCAT('/cache/image?id=',fanart) AS fanart, rating, premiered, genre, scraperName, scraperID, path, multipleResults, (SELECT COUNT(st.idView) FROM movies mov LEFT JOIN mov_status st ON (st.idMovie = mov.idMovie) WHERE idUser = "+str(idUser)+") AS viewCount, CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND dataType = 'movies'),scraperID) AS scraperLink FROM movies t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;")
        return cursor.fetchall()

    def mov_setID(self, idMovie, resultID):
        #the resultID is the one from the json list of multipleResults entry
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT multipleResults FROM movies WHERE idMovie = "+str(idMovie)+";")
        data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
        cursor.execute("UPDATE movies SET scraperName = %s, scraperID = %s, scraperData = %s, forceUpdate = 1, multipleResults = NULL WHERE idMovie = %s;", (data["scraperName"], data["id"], data["scraperData"], idMovie))
        self._connection.commit()
        return True
        
    def mov_refreshCache(self):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT icon, fanart FROM movies;")
        data = cursor.fetchall()
        for d in data:
            if d["icon"] != None:
                self.addCache(d["icon"])
            if d["fanart"] != None:
                self.addCache(d["fanart"])