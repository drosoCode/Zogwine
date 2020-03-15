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

from indexer import scanner
from log import logger

class api:

    def __init__(self, configFile):
        with open(configFile) as f:
            data = json.load(f)
            self._data = data
            self._connection = sql(host=data["db"]["host"],user=data["db"]["user"],password=data["db"]["password"],database='mediaController')
            self._scanner = scanner(self._connection, 'tvs', data["api"])
            self._fileDuration = {}
            self._userProcess = {}
            self._userTokens = {}
        logger.info('API Class Instancied Successfully')

    def getTVSData(self, token, mr=False):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        mrDat = ''
        if mr:
            mrDat = 'NOT '
        cursor.execute("SELECT idShow AS id, title, overview, icon, fanart, rating, premiered, genre, scraperName, scraperID, path, multipleResults, (SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons, (SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes, (SELECT COUNT(v.idView) FROM episodes e LEFT JOIN views v ON (v.idEpisode = e.idEpisode) WHERE e.idShow = t.idShow AND viewCount > 0  AND idUser = "+str(idUser)+") AS viewedEpisodes, CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName),scraperID) AS scraperLink FROM tv_shows t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;")
        return cursor.fetchall()
    
    def getTVSEp(self, idShow, token):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT idEpisode AS id, title, overview, icon, season, episode, rating, scraperName, scraperID, (SELECT viewCount FROM views WHERE idEpisode = e.idEpisode AND idUser = "+str(idUser)+") AS viewCount FROM episodes e WHERE idShow = "+str(idShow)+" ORDER BY season, episode;")
        return cursor.fetchall()
    
    def setTVSID(self, idShow, resultID):
        #the resultID is the one from the json list of multipleResults entry
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT multipleResults FROM tv_shows WHERE idShow = "+str(idShow)+";")
        data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
        cursor.execute("UPDATE tv_shows SET scraperName = %s, scraperID = %s, forceUpdate = 1, multipleResults = NULL WHERE idShow = %s;", (data["scraperName"], data["id"], idShow))
        self._connection.commit()
        return True

    def runScan(self):
        self._scanner.scanDir(self._data["config"]["tvsDirectory"])
        return True

    def getFileInfos(self, episodeID):        
        epPath = self.getEpPath(episodeID)
        cmd = "ffprobe -v quiet -print_format json -show_format -show_streams \""+epPath+"\" > out/data.json"

        logger.debug('FFprobe: '+cmd)
        os.system(cmd)

        with open("out/data.json","r", encoding='utf-8') as f:
            dat = json.load(f, encoding='UTF8')

        data = {
            "general":{
                "format": dat["format"]["format_name"],
                "duration": dat["format"]["duration"],
                "extension": epPath[epPath.rfind('.')+1:]
            },
            "audio":[],
            "subtitles":[]
        }

        for stream in dat["streams"]:
            lang = ''
            if stream["codec_type"] == "video":
                data["general"]["video_codec"] = stream["codec_name"]
            elif stream["codec_type"] == "audio":
                if 'language' in stream["tags"]:
                    lang = stream["tags"]["language"]
                data["audio"].append({"index":stream["index"], "codec":stream["codec_name"], "channels":stream["channels"], "language": lang})
            elif stream["codec_type"] == "subtitle":
                t = ''
                if 'title' in stream["tags"]:
                    t = stream["tags"]["title"]
                if 'language' in stream["tags"]:
                    lang = stream["tags"]["language"]
                data["subtitles"].append({"index":stream["index"], "codec":stream["codec_name"], "language": lang, "title": t})

        self._fileDuration[episodeID] = dat["format"]["duration"]
        return data

    def getEpPath(self, idEpisode):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT CONCAT(t.path, '/', e.path) AS path FROM tv_shows t INNER JOIN episodes e ON t.idShow = e.idShow WHERE e.idEpisode = "+str(idEpisode)+";")
        path = self._data["config"]["tvsDirectory"]+'/'+cursor.fetchone()['path']
        logger.debug('Getting episode path for id:'+str(idEpisode)+' -> '+path)
        return path

    def startTranscoder(self, idEpisode, token, audioStream, subStream, subTxt):
        logger.info('Starting transcoder for episode '+str(idEpisode)+' and user '+str(self._userTokens[token]))
        path = '"'+self.getEpPath(idEpisode)+'"'

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
        hlsTime = str(self._data["config"]['hlsTime']) #in seconds
        
        if '..' not in path:
            if subStream != "-1":
                if subTxt == "1":
                    cmd = " -vsync 0 -i " + path + " -pix_fmt yuv420p -vf subtitles=" + path.replace(":","\\\\:") +" -c:a aac -ar 48000 -b:a 128k -pix_fmt yuv420p -c:v h264_nvenc -map 0:a:" + audioStream + " -map 0:v:0 -map 0:s:" + subStream + " -crf " + crf + " -hls_time "+hlsTime+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"
                else:
                    cmd = " -i " + path +" -pix_fmt yuv420p -preset medium -filter_complex \"[0:v][0:s:" + subStream + "]overlay[v]\" -map \"[v]\" -map 0:a:" + audioStream + " -c:a aac -ar 48000 -b:a 128k -c:v h264_nvenc -crf " + crf + " -hls_time "+hlsTime+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"
            else:
                cmd = " -vsync 0 -i " + path + " -pix_fmt yuv420p -c:a aac -ar 48000 -b:a 128k -pix_fmt yuv420p -c:v h264_nvenc -map 0:a:" + audioStream + " -map 0:v:0 -crf " + crf + " -hls_time "+str(hlsTime)+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"

            cmd = "ffmpeg -hide_banner -loglevel error" + cmd
            print(cmd)
            #process = Popen(cmd, creationflags=CREATE_NEW_CONSOLE)
            process = Popen("exec "+cmd, shell=True)
            self._userProcess[token] = process
            print(self._userProcess)

            return True
        else:
            return False
    
    def stopTranscoder(self, token):
        logger.info('Stopping transcoder for user '+str(self._userTokens[token]))
        if token in self._userProcess:
            self._userProcess[token].kill()
            del self._userProcess[token]
            
        if token != "" and ".." not in token:
            #shutil.rmtree('out/'+token)
            os.system("rm -rf \"out/"+token+"\"")
            os.system("rm -rf \"out/"+token+"\"")

    def setViewedTime(self, idEpisode, token, lastRequestedFile):
        timeSplit = int(self._data["config"]["hlsTime"])
        if lastRequestedFile is not None and idEpisode in self._fileDuration:
            d = float(self._fileDuration[idEpisode])
            num = int(re.findall("(?i)(?:stream)(\\d+)(?:\\.ts)", lastRequestedFile)[0]) + 1

            logger.debug('Setting viewed status for user '+str(self._userTokens[token])+' : '+str(d)+' '+str(num)+' '+str(num*timeSplit)+' '+str(d - (d/100*2)))

            if d is not None and num*timeSplit > d - (d/100*10):
                self.toggleViewed(idEpisode, token, True)
            del self._fileDuration[idEpisode]
            return True
        else:
            return False

    def toggleViewedTVS(self, idShow, token, season='all', add=None):
        ids = self.getTVSEp(idShow, token)
        for i in ids:
            if season == 'all' or int(season) == int(i["season"]):
                self.toggleViewed(i["id"],token,add)
        return True

    def toggleViewed(self, idEpisode, token, add=None):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT viewCount FROM views WHERE idUser = '"+str(self._userTokens[token])+"' AND idEpisode = '"+str(idEpisode)+"';")
        data = cursor.fetchone()
        count = 0
        if data != None and "viewCount" in data:
            #update
            count = data["viewCount"]
            if add == None:
                if count > 0:
                    count = 0
                else:
                    count = 1
            elif add:
                count += 1
            else:
                count -= 1
            cursor.execute("UPDATE views SET viewCount = %s WHERE idUser = %s AND idEpisode = %s;", (str(count), str(self._userTokens[token]), str(idEpisode)))
        else:
            cursor.execute("INSERT INTO views (idUser, idEpisode, viewCount) VALUES (%s, %s, 1);", (str(self._userTokens[token]), str(idEpisode)))
        self._connection.commit()
        return True

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
        cursor.execute("SELECT COUNT(idView) AS watchedEpCount, SUM(viewCount) AS watchedEpSum FROM views WHERE viewCount > 0 AND idUser = "+str(self._userTokens[token])+";")
        dat1 = cursor.fetchone()
        cursor.execute("SELECT COUNT(DISTINCT idShow) AS tvsCount, COUNT(idEpisode) AS epCount FROM episodes;")
        dat2 = cursor.fetchone()
        if "watchedEpSum" not in dat1 or dat1["watchedEpSum"] == None:
            dat1["watchedEpSum"] = 0
        return {"watchedEpCount":int(dat1["watchedEpCount"]), "watchedEpSum":int(dat1["watchedEpSum"]), "tvsCount":int(dat2["tvsCount"]), "epCount": int(dat2["epCount"]), "lostTime": avgEpTime * int(dat1["watchedEpSum"])}
    