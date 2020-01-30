import requests
import mysql.connector as sql
from indexer import scanner
import json
import os
from wakeonlan import send_magic_packet
import time
import base64
import hashlib
import re
import urllib.parse

from log import logger

class api:

    def __init__(self, configFile):
        with open(configFile) as f:
            data = json.load(f)
            self._data = data
            self._connection = sql.connect(host=data["db"]["host"],user=data["db"]["user"],password=data["db"]["password"],database='mediaController')
            self._scanner = scanner(data["db"]["host"],data["db"]["user"], data["db"]["password"], data["api"]["tmdb"], data["api"]["tvdb"])
            self._fileDuration = {}
        logger.info('API Class Instancied Successfully')

    def getTVSData(self, mr=False):
        cursor = self._connection.cursor(dictionary=True)
        mrDat = ''
        if mr:
            mrDat = 'NOT '
        cursor.execute("SELECT idShow AS id, title, overview, icon, fanart, rating, premiered, genre, scraperName, scraperID, path, multipleResults, (SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons, (SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes, (SELECT COUNT(idView) FROM views WHERE idShow = t.idShow AND idEpisode IS NOT NULL AND viewCount > 0) AS viewedEpisodes, CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName),scraperID) AS scraperLink FROM tv_shows t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;")
        return cursor.fetchall()
    
    def getTVSEp(self, idShow):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT idEpisode AS id, title, overview, icon, season, episode, rating, scraperName, scraperID, (SELECT viewCount FROM views WHERE idEpisode = e.idEpisode AND idShow = e.idShow) AS viewCount FROM episodes e WHERE idShow = "+str(idShow)+" ORDER BY season, episode;")
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
        self._scanner.scanDir(self._data["paths"]["scanDirectory"])
        return True

    def getFileInfos(self, episodeID):        
        epPath = self.getEpPath(episodeID)
        cmd = " -v quiet -print_format json -show_format -show_streams \""+epPath+"\" > out/data.json"
        if os.name == 'nt':
            #windows
            cmd = 'ffprobe.exe'+cmd
        else:
            cmd = './ffprobe'+cmd

        logger.debug('FFprobe: '+cmd)
        os.system(cmd)

        with open("out/data.json","r") as f:
            dat = json.load(f)

        data = {
            "general":{
                "format": dat["format"]["format_long_name"],
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

    def getEpPath(self, idEpisode, full=True):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT CONCAT(t.path, '/', e.path) AS path FROM tv_shows t INNER JOIN episodes e ON t.idShow = e.idShow WHERE e.idEpisode = "+str(idEpisode)+";")
        path = cursor.fetchone()['path']
        if full:
            path = self._data["paths"]["scanDirectory"]+'/'+path
        logger.debug('Getting episode path for id:'+str(idEpisode)+' -> '+path)
        return path
        
    def getTranscoderUrl(self):
        return self._data["paths"]["transcoderURL"]

    def startTranscoder(self, idEpisode, token, audioStream, subStream, subTxt):
        success = False
        trys = 0
        while not success and trys < 4:
            try:
                if requests.get(self._data["paths"]["transcoderURL"]+"/ping").text == "pong":
                    success = True
            except:
                pass
            if not success and trys == 0:
                mac = self._data["paths"]["transcoderMAC"]
                mac = mac.replace(":",".")
                send_magic_packet(mac)
            time.sleep(10)
            trys += 1
        if not success:
            return False
        else:
            path = urllib.parse.quote(base64.b64encode(bytes(self.getEpPath(idEpisode, False), encoding='utf-8')).decode("utf-8"))
            url = self._data["paths"]["transcoderURL"]+"/transcoder/start?token="+token+"&file="+path+"&audioStream="+audioStream+"&subStream="+subStream+"&subTxt="+subTxt
            print(url)
            requests.get(url)
            return True

    def setViewedTime(self, idEpisode, token, lastRequestedFile):
        timeSplit = int(requests.get(self.getTranscoderUrl()+"/transcoder/getHLSTime").text)
        if lastRequestedFile is not None and d is not None and idEpisode in self._fileDuration:
            d = int(self._fileDuration[idEpisode])
            num = int(re.findall("(?i)(?:stream)(\\d+)(?:\\.ts)", lastRequestedFile)[0])
            if num*timeSplit > d - (d/100*2):
                self.setViewed(idEpisode, token)
            del self._fileDuration[idEpisode]
            return True
        else:
            return False


    def setViewed(self, idEpisode, token):
        return True

    def getUserData(self,token):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT name, icon, admin, kodiLinkBase FROM users WHERE token = '"+str(token)+"';")
        return cursor.fetchone()

    def authenticateUser(self, user, password):
        password = hashlib.sha256(bytes(password, 'utf-8')).hexdigest()
        cursor = self._connection.cursor(dictionary=True)
        if user != "" and password != "":
            r = "SELECT token FROM users WHERE user = '"+str(user)+"' AND password = '"+str(password)+"';"
            cursor.execute(r)
            dat = cursor.fetchone()
            if dat != None and "token" in dat:
                logger.info('User: '+str(user)+' successfully authenticated')
                return dat["token"]
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