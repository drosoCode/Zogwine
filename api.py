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

"""
DB:
    mediaType: 1=tv_show ep
               2=tv_show
               3=movie
               
"""

class api:

    def __init__(self, configFile):
        with open(configFile) as f:
            data = json.load(f)
            self._data = data
            self._connection = sql(host=data["db"]["host"],user=data["db"]["user"],password=data["db"]["password"],database=data["db"]["name"], use_unicode=True, charset='utf8')
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
        cursor.execute("SELECT COUNT(idStatus) AS watchedEpCount, SUM(watchCount) AS watchedEpSum FROM status WHERE watchCount > 0 AND mediaType = 1 AND idUser = %(idUser)s;", {'idUser': self._userTokens[token]})
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
                logger.debug('Adding '+file+' to cache')
                f.write(requests.get(b64decode(data).decode()).content)

    def refreshCache(self):
        self.tvs_refreshCache()
        self.mov_refreshCache()

        cursor = self._connection.cursor(dictionary=True)
        #refresh tags cache
        cursor.execute("SELECT icon FROM tags;")
        data = cursor.fetchall()
        for d in data:
            if d["icon"] != None:
                self.addCache(d["icon"])
        #refresh persons cache
        cursor.execute("SELECT icon FROM persons;")
        data = cursor.fetchall()
        for d in data:
            if d["icon"] != None:
                self.addCache(d["icon"])


    def runScan(self):
        self.tvs_runScan()
        #self.mov_runScan()


    def getPersons(self, mediaType, idMedia):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT p.idPers, role, name, gender, birthdate, deathdate, description, CONCAT('/cache/image?id=',icon) AS icon " \
                        "FROM persons p, persons_link l " \
                        "WHERE p.idPers = l.idPers" \
                        " AND mediaType = %(mediaType)s AND idMedia = %(idMedia)s;", {'mediaType': mediaType, 'idMedia': idMedia})
        return cursor.fetchall()

    def getTags(self, mediaType, idMedia):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT t.idTag, name, value, CONCAT('/cache/image?id=',icon) AS icon " \
                        "FROM tags t, tags_link l " \
                        "WHERE t.idTag = l.idTag" \
                        " AND mediaType = %(mediaType)s AND idMedia = %(idMedia)s;", {'mediaType': mediaType, 'idMedia': idMedia})
        return cursor.fetchall()

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
                    "(SELECT COUNT(*) FROM episodes e LEFT JOIN status s ON (s.idMedia = e.idEpisode) "\
                        "WHERE e.idEpisode = s.idMedia AND s.mediaType = 1 AND watchCount > 0  AND idUser = %(idUser)s AND idShow = t.idShow) AS watchedEpisodes "\
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
                    "(SELECT COUNT(*) FROM episodes e LEFT JOIN status s ON (s.idMedia = e.idEpisode)" \
                        "WHERE e.idEpisode = s.idMedia AND s.mediaType = 1 AND watchCount > 0  AND idUser = %(idUser)s and idShow = t.idShow) AS watchedEpisodes," \
                    "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 'tv_shows'),scraperID) AS scraperLink " \
                    "FROM tv_shows t " \
                    "WHERE multipleResults IS NULL AND idShow = %(idShow)s ORDER BY title;"
        cursor.execute(query, {'idUser': str(idUser), 'idShow': str(idShow)})
        return cursor.fetchone()    

    def tvs_getSeasons(self, token, idShow):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT title, overview, CONCAT('/cache/image?id=',icon) AS icon," \
                        "season, premiered, "\
                        "(SELECT COUNT(*) FROM episodes WHERE idShow = s.idShow AND season = s.season) AS episodes, "
                        "(SELECT COUNT(watchCount) FROM status WHERE idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = s.idShow AND season = s.season) AND mediaType = 1 AND idUser = %(idUser)s) AS watchedEpisodes " \
                       "FROM seasons s "\
                       "WHERE idShow = %(idShow)s " \
                       "ORDER BY season;", {'idUser': idUser, 'idShow': idShow})
        return cursor.fetchall()
    
    def tvs_getEps(self, token, idShow, season=None):
        idUser = self._userTokens[token]
        cursor = self._connection.cursor(dictionary=True)
        s = ''
        dat = {'idUser': idUser, 'idShow': idShow}
        if season is not None:
            dat['season'] = season
            s = "AND season = %(season)s "
        cursor.execute("SELECT idEpisode AS id, title, overview, CONCAT('/cache/image?id=',icon) AS icon," \
                        "season, episode, rating, scraperName, scraperID, "\
                        "(SELECT watchCount FROM status WHERE idMedia = e.idEpisode AND mediaType = 1 AND idUser = %(idUser)s) AS watchCount " \
                       "FROM episodes e "\
                       "WHERE idShow = %(idShow)s " + s + "" \
                       "ORDER BY season, episode;", dat)
        return cursor.fetchall()

    def tvs_getNextEps(self):
        scan = scanner(self._connection, 'tvs', self._data["api"])
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT idShow, title, scraperName, scraperID, fanart " \
                       "FROM tv_shows "\
                       "WHERE multipleResults IS NULL")
        data = {}
        for tvs in cursor.fetchall():
            ep = scan.getTvsNextEps(tvs['scraperName'], tvs['scraperID'])
            if ep is not None:
                ep['idShow'] = tvs['idShow']
                ep['showTitle'] = tvs['title']
                if ep['icon'] is None:
                    ep['icon'] = tvs['fanart']
                data[ep['date']] = ep
        ret = []
        for d in sorted(data):
            ret.append(data[d])
        return ret
    
    def tvs_setID(self, idShow, resultID):
        #the resultID is the one from the json list of multipleResults entry
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT multipleResults FROM tv_shows WHERE idShow = %(idShow)s;", {'idShow': str(idShow)})
        data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
        cursor.execute("UPDATE tv_shows SET scraperName = %(scraperName)s, scraperID = %(scraperId)s, scraperData = %(scraperData)s, forceUpdate = 1, multipleResults = NULL WHERE idShow = %(idShow)s;", {'scraperName': data["scraperName"], 'scraperId': data["id"], 'scraperData': data["scraperData"], 'idShow': idShow})
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
        cursor.execute("SELECT viewTime FROM tvs_status WHERE idUser = %(idUser)s AND idEpisode = %(idEpisode)s;", {'idUser': self._userTokens[token], 'idEpisode': episodeID})
        data = cursor.fetchone()
        if data != None and "viewTime" in data:
            tr.setStartTime(float(data["viewTime"]))

        self._userFiles[token] = tr
        return tr.getFileInfos()

    def tvs_getEpPath(self, idEpisode):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT CONCAT(t.path, '/', e.path) AS path FROM tv_shows t INNER JOIN episodes e ON t.idShow = e.idShow WHERE e.idEpisode = %(idEpisode)s;", {'idEpisode': idEpisode})
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
        cursor.execute("SELECT idStatus, watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idEpisode)s;", {'idUser': self._userTokens[token], 'idEpisode': idEpisode})
        data = cursor.fetchone()
        viewAdd = 0
    
        if endTime > d * self._data['config']['watchedThreshold']:
            viewAdd = 1

        if data != None and "watchCount" in data:
            cursor.execute("UPDATE status SET watchCount = %(watchCount)s, watchTime = %(watchTime)s WHERE idStatus = %(idStatus)s;", {'watchCount':str(data["watchCount"]+viewAdd), 'watchTime': str(endTime), 'idStatus': str(data["idStatus"])})
        else:
            cursor.execute("INSERT INTO tvs_status (idUser, idEpisode, watchCount, watchTime) VALUES (%s, %s, 1, %s);", (str(self._userTokens[token]), str(idEpisode), str(viewAdd), str(endTime)))

        del self._userFiles[token]

        return True

    def tvs_toggleViewed(self, idShow, token, season='all'):
        ids = self.tvs_getEps(idShow, token)
        for i in ids:
            if season == 'all' or int(season) == int(i["season"]):
                self.tvs_toggleViewedEp(i["id"],token)
        return True

    def tvs_toggleViewedEp(self, idEpisode, token):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idEpisode)s;", {'idEpisode': str(idEpisode), 'idUser': str(self._userTokens[token])})
        data = cursor.fetchone()
        count = 0
        if data != None and "watchCount" in data:
            #update
            count = data["watchCount"]
            if count > 0:
                count = 0
            else:
                count = 1
            cursor.execute("UPDATE status SET watchCount = %(watchCount)s WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idMedia)s;", {'watchCount': str(count), 'idUser': str(self._userTokens[token]), 'idMedia': str(idEpisode)})
        else:
            cursor.execute("INSERT INTO status (idUser, mediaType, idMedia, watchCount) VALUES (%(idUser)s, 1, %(idMedia)s, 1);", {'idUser': str(self._userTokens[token]), 'idMedia': str(idEpisode)})
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
        cursor.execute("SELECT icon FROM seasons;")
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
        cursor.execute("SELECT idMovie AS id, title, overview, CONCAT('/cache/image?id=',icon) AS icon, CONCAT('/cache/image?id=',fanart) AS fanart, rating, premiered, genre, scraperName, scraperID, path, multipleResults, (SELECT COUNT(st.idStatus) FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3) AS viewCount, CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 'movies'),scraperID) AS scraperLink FROM movies t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;", {'idUser': idUser})
        return cursor.fetchall()

    def mov_setID(self, idMovie, resultID):
        #the resultID is the one from the json list of multipleResults entry
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT multipleResults FROM movies WHERE idMovie = "+str(idMovie)+";")
        data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
        cursor.execute("UPDATE movies SET scraperName = %(scraperName)s, scraperID = %(scraperID)s, scraperData = %(scraperData)s, forceUpdate = 1, multipleResults = NULL WHERE idMovie = %(idMovie)s;", {'scraperName': data["scraperName"], 'scraperID': data["id"], 'scraperData': data["scraperData"], 'idMovie': idMovie})
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