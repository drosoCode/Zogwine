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
from transcoder import transcoder

class api:

    def __init__(self, configFile):
        with open(configFile) as f:
            data = json.load(f)
            self._data = data
            self._connection = sql(host=data["db"]["host"],user=data["db"]["user"],password=data["db"]["password"],database='mediaController')
            self._userFiles = {}
            self._userTokens = {}
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

    def tvs_getShows(self, token, mr=False):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        mrDat = ''
        if mr:
            mrDat = 'NOT '
        query = "SELECT idShow AS id, title,"\
                    "CONCAT('/cache/image?id=',icon) AS icon,"\
                    "rating, premiered, genre, multipleResults,"\
                    "(SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons,"\
                    "(SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes,"\
                    "(SELECT COUNT(v.idView) FROM episodes e LEFT JOIN tvs_status v ON (v.idEpisode = e.idEpisode) "\
                        "WHERE e.idShow = t.idShow AND viewCount > 0  AND idUser = %(idUser)s) AS watchedEpisodes "\
                    "FROM tv_shows t "\
                    "WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;"
        cursor.execute(query, {'idUser': str(idUser)})
        return cursor.fetchall()
        
    def tvs_getShow(self, token, idShow):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        query = "SELECT idShow AS id," \
                    "title, overview, " \
                    "CONCAT('/cache/image?id=',icon) AS icon, " \
                    "CONCAT('/cache/image?id=',fanart) AS fanart, " \
                    "rating, premiered, genre, scraperName, scraperID, path," \
                    "(SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons," \
                    "(SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes," \
                    "(SELECT COUNT(v.idView) FROM episodes e LEFT JOIN tvs_status v ON (v.idEpisode = e.idEpisode)" \
                        "WHERE e.idShow = t.idShow AND viewCount > 0  AND idUser = %(idUser)s) AS watchedEpisodes," \
                    "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND dataType = 'tv_shows'),scraperID) AS scraperLink " \
                    "FROM tv_shows t " \
                    "WHERE multipleResults IS NULL AND idShow = %(idShow)s ORDER BY title;"
        cursor.execute(query, {'idUser': str(idUser), 'idShow': str(idShow)})
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
        epPath = self.tvs_getEpPath(episodeID)
        tr = transcoder(epPath, self._data['config']['outDir']+'/'+token, self._data['config']['encoder'], self._data['config']['crf'])

        #get last view end if available
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT viewTime FROM tvs_status WHERE idUser = '"+str(self._userTokens[token])+"' AND idEpisode = '"+str(episodeID)+"';")
        data = cursor.fetchone()
        if data != None and "viewTime" in data:
            tr.setStartTime(float(data["viewTime"]))

        self._userFiles[token] = tr
        return tr.getFileInfos()

    def tvs_getEpPath(self, idEpisode):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT CONCAT(t.path, '/', e.path) AS path FROM tv_shows t INNER JOIN episodes e ON t.idShow = e.idShow WHERE e.idEpisode = "+str(idEpisode)+";")
        path = self._data["config"]["tvsDirectory"]+'/'+cursor.fetchone()['path']
        logger.debug('Getting episode path for id:'+str(idEpisode)+' -> '+path)
        return path

    def tvs_startTranscoder(self, idEpisode, token, audioStream, subStream, startFrom=0, resize=-1):
        logger.info('Starting transcoder for user '+str(self._userTokens[token]))

        self._userFiles[token].setAudioStream(audioStream)
        self._userFiles[token].setSub(subStream)
        self._userFiles[token].enableHLS(True, self._data["config"]['hlsTime'])
        self._userFiles[token].setStartTime(startFrom)
        self._userFiles[token].resize(resize)
        self._userFiles[token].start()

        return True
    
    def tvs_stopTranscoder(self, token):
        logger.info('Stopping transcoder for user '+str(self._userTokens[token]))
        self._userFiles[token].stop()

    def tvs_setViewedTime(self, idEpisode, token, lastRequestedFile, endTime=-1):

        if endTime == -1:
            endTime = self._userFiles[token].getWatchedDuration(lastRequestedFile)
        else:
            endTime = self._userFiles[token].getWatchedDuration(endTime)
        d = float(self._userFiles[token].getFileInfos()['general']['duration'])

        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT idView, viewCount FROM tvs_status WHERE idUser = '"+str(self._userTokens[token])+"' AND idEpisode = '"+str(idEpisode)+"';")
        data = cursor.fetchone()
        viewAdd = 0
    
        if endTime > d * self._data['config']['watchedThreshold']:
            viewAdd = 1

        if data != None and "viewCount" in data:
            droso = (str(data["viewCount"]+viewAdd), str(endTime), str(data["idView"]))
            print(droso)
            cursor.execute("UPDATE tvs_status SET viewCount = %s, viewTime = %s WHERE idView = %s;", droso)
        else:
            cursor.execute("INSERT INTO tvs_status (idUser, idEpisode, viewCount, viewTime) VALUES (%s, %s, 1, %s);", (str(self._userTokens[token]), str(idEpisode), str(viewAdd), str(endTime)))

        del self._userFiles[token]

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