import mysql.connector as sql
import re
import os
import json
import requests
import urllib.parse

from scraper_tvdb import tvdb
from scraper_tmdb import tmdb
from log import logger


class scanner:

    def __init__(self, host, user, passw, tmdbKey, tvdbKey):
        self._supportedFiles = ["mkv","mp4","avi"]
        self._connection = sql.connect(host=host,user=user,password=passw,database='mediaController')
        self._tvdb = tvdb(tvdbKey)
        self._tmdb = tmdb(tmdbKey)
        self._currentTVS = None
        logger.info('Indexer Class Instancied Successfully')
        logger.info('Supported file formats: '+str(self._supportedFiles))

    def getTVSData(self):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tv_shows ORDER BY title;")
        dat = cursor.fetchall()
        paths = []
        tvs = {}
        for i in dat:
            paths.append(i["path"])
            tvs[i["path"]] = i
        return paths, tvs

    def scanDir(self, path, recursive=False, addPath=""):
        logger.info('Scan Dir Triggered, recursive: '+str(recursive)+' ; current TVS: '+str(self._currentTVS)+' ; additionnalPath: '+addPath)
        dirContent = os.listdir(path)
        self._existingEp = []
        self._forceUpdateEp = []
        self._idUpdateEp = {}
        self._paths, self._tvs = self.getTVSData()
        cursor = self._connection.cursor(dictionary=True)
        
        for item in dirContent:
            #try:
                commit = False
                logger.debug('New Item: '+str(item))

                if os.path.isdir(os.path.join(path,item)):
                    logger.debug('Item is a directory')
                    
                    if recursive:
                        #we are inside a tvs dir, so it is a season directory
                        logger.debug('D- It is a season directory (recursive call)')
                        if addPath != '':
                            newAddPath = addPath + '/' + item
                        else:
                            newAddPath = item
                        logger.debug('Path inside tvs directory: '+str(newAddPath))
                        self.scanDir(os.path.join(path,item), True, newAddPath)
                    else:
                        #it is a tvs directory
                        logger.debug('D- It is a TVS root directory')
                        self.scanTVS(path, item)
                        
                else:
                    logger.debug('Item is a file')
                    if len(self._existingEp) == 0 and len(self._forceUpdateEp) == 0 and len(self._idUpdateEp) == 0:
                        #fill the buffer with episodes that mustn't be updated
                        cursor.execute("SELECT CONCAT(season,'.',episode) AS epCode, idEpisode, forceUpdate from episodes WHERE idShow = "+str(self._tvs[self._currentTVS]["idShow"])+";")
                        dat = cursor.fetchall()
                        for i in dat:
                            self._existingEp.append(i["epCode"])
                            if i['forceUpdate']:
                                self._forceUpdateEp.append(i["epCode"])
                                self._idUpdateEp[i["epCode"]] = i["idEpisode"]

                        logger.debug('Existing episodes: '+str(self._existingEp))
                        logger.debug('Force Update episodes: '+str(self._forceUpdateEp))
                        logger.debug('ID Update episodes: '+str(self._idUpdateEp))

                    #it is an episode file
                    logger.debug("this is an episode file")
                    self.scanEpisode(addPath,item)

                if commit:
                    self._connection.commit()
                    logger.debug(str(cursor.rowcount)+' rows affected')
            #except Exception as ex:
            #    logger.error('New indexer exception: '+str(ex))
                
        logger.debug('End of scan (recursive: '+str(recursive)+')')
    

    def scanTVS(self, path, item):
        cursor = self._connection.cursor(dictionary=True)
        commit = False

        if item in self._paths:
            logger.debug('D- Entries for this item exists in database')

            if self._tvs[item]["forceUpdate"] and self._tvs[item]["scraperName"] and self._tvs[item]["scraperID"]:
                logger.debug('D- Item is marked as force update')
                #tvs must be updated
                if self._tvs[item]["scraperName"] == "tvdb":
                    result = self._tvdb.getTVS(self._tvs[item]["scraperID"])
                else:
                    result = self._tmdb.getTVS(self._tvs[item]["scraperID"])

                data = (result["title"], result["desc"], result["icon"], result["fanart"], result["rating"], result["premiered"], json.dumps(result["genres"]), item, self._tvs[item]["idShow"])
                cursor.execute("UPDATE tv_shows SET title = %s, overview = %s, icon = %s, fanart = %s, rating = %s, premiered = %s, genre = %s, path = %s, forceUpdate = 0, multipleResults = NULL WHERE idShow = %s;", data)
                commit = True

                logger.debug('Updating database with: '+str(data))

            elif self._tvs[item]["multipleResults"]:
                #there are multiple matches for scraper, cannot create entries
                logger.debug('D- Item match multipleResults, ignoring')
            else:
                #tvs is ok, call scan on tvs folder
                self._currentTVS = item
                self.scanDir(os.path.join(path,item), True)
                logger.debug('D- Item ok, scanning subdirectories')
        else:
            #entries for this tvs doesn't exists, create entry with multipleResults
            logger.debug('Entries for this item doesn\'t exists in database')
            a = self._tvdb.searchTVS(item)
            b = self._tmdb.searchTVS(item)
            if isinstance(a,dict):
                a = [a]
            if isinstance(b,dict):
                b = [b]
            results = a + b
            logger.debug('The multipleResults are: '+str(results))
            cursor.execute("INSERT INTO tv_shows (multipleResults, path) VALUES (%s, %s);", (json.dumps(results), item))
            commit = True

        if commit:
            self._connection.commit()
            logger.debug(str(cursor.rowcount)+'were affected')


    def scanEpisode(self, path, item):
        extension = item[item.rfind('.')+1:]
        logger.debug('The extension for: '+self._currentTVS+' is: '+extension)
        cursor = self._connection.cursor(dictionary=True)
        commit = False

        if extension in self._supportedFiles and self._currentTVS:
            logger.debug('This is a supported file')
            #create entry for episode
            season = re.findall("(?i)(?:s)(\\d+)(?:e)", item)
            episode = re.findall("(?i)(?:s\\d+e)(\\d+)(?:\\.)", item)
            if len(season) > 0 and len(episode) > 0:
                season = int(season[0])
                episode = int(episode[0])
                epCode = str(season)+"."+str(episode)

                logger.debug('The episode code is: '+str(epCode))

                if epCode not in self._existingEp or epCode in self._forceUpdateEp:
                    logger.debug('No entries are available for this episode or it is marked as forceUpdate')
                    #create empty dict
                    result = {'title': None,'desc': None, 'icon': None, 'season': None, 'episode': None, 'rating': None,'id': None}
                    
                    if self._tvs[self._currentTVS]["scraperName"] == "tvdb":
                        logger.debug('Getting tvdb results')
                        result.update(self._tvdb.getTVSEp(self._tvs[self._currentTVS]["scraperID"],season,episode))
                    else:
                        logger.debug('Getting tbdb results')
                        result.update(self._tmdb.getTVSEp(self._tvs[self._currentTVS]["scraperID"],season,episode))

                    forceUpdate = 0
                    if "desc" not in result or ("desc" in result and result["desc"] == ""):
                        logger.debug('Episode overview not available, setting as future forceUpdate')
                        forceUpdate = 1

                    if result['id'] != None:
                        if path != '':
                            filePath = path + '/' + item
                        else:
                            filePath = item

                        if epCode not in self._existingEp:
                            logger.debug('Creating new entry')
                            data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], self._tvs[self._currentTVS]["scraperName"], result["id"], filePath, self._tvs[self._currentTVS]["idShow"], forceUpdate)
                            cursor.execute("INSERT INTO episodes (title, overview, icon, season, episode, rating, scraperName, scraperID, path, idShow, forceUpdate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",data)
                            commit = True

                        elif epCode in self._forceUpdateEp:
                            logger.debug('Updating existing entry (forceUpdate)')
                            data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], self._tvs[self._currentTVS]["scraperName"], result["id"], filePath, self._tvs[self._currentTVS]["idShow"], forceUpdate, self._idUpdateEp[epCode])                        
                            cursor.execute("UPDATE episodes SET title = %s, overview = %s, icon = %s, season = %s, episode = %s, rating = %s, scraperName = %s, scraperID = %s, path = %s, idShow = %s, forceUpdate = %s WHERE idEpisode = %s;", data)
                            commit = True

                        logger.debug('Updating database with: '+str(data))
                    else:
                        logger.warning('Episode ID is null') 
                else:
                    logger.debug('Entries for this episode already exists') 
            else:
                logger.warning('Cannot extract season or episode from file name')

        if commit:
            self._connection.commit()
            logger.debug(str(cursor.rowcount)+'were affected')