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

    def scanDir(self,path, recursive=False, currentTVS=None):
        logger.info('Scan Dir Triggered, recursive: '+str(recursive)+' ; current TVS: '+str(currentTVS))
        dirContent = os.listdir(path)
        existingEp = []
        forceUpdateEp = []
        idUpdateEp = {}
        paths, tvs = self.getTVSData()
        cursor = self._connection.cursor(dictionary=True)
        
        for item in dirContent:
            try:
                commit = False
                logger.debug('New Item: '+str(item))

                if os.path.isdir(os.path.join(path,item)):
                    logger.debug('Item is a directory')
                    
                    if recursive:
                        #it is a season directory
                        logger.debug('D- It is a season directory (recursive call)')
                        self.scanDir(os.path.join(path,item), True, currentTVS)
                    else:
                        #it is a tvs directory
                        logger.debug('D- It is a TVS root directory')

                        if item in paths:
                            logger.debug('D- Entries for this item exists in database')

                            if tvs[item]["forceUpdate"] and tvs[item]["scraperName"] and tvs[item]["scraperID"]:
                                logger.debug('D- Item is marked as force update')
                                #tvs must be updated
                                if tvs[item]["scraperName"] == "tvdb":
                                    result = self._tvdb.getTVS(tvs[item]["scraperID"])
                                else:
                                    result = self._tmdb.getTVS(tvs[item]["scraperID"])
                                data = (result["title"], result["desc"], result["icon"], result["fanart"], result["rating"], result["premiered"], json.dumps(result["genres"]), item, tvs[item]["idShow"])
                                cursor.execute("UPDATE tv_shows SET title = %s, overview = %s, icon = %s, fanart = %s, rating = %s, premiered = %s, genre = %s, path = %s, forceUpdate = 0, multipleResults = NULL WHERE idShow = %s;", data)
                                commit = True
                            elif tvs[item]["multipleResults"]:
                                #there are multiple matches for scraper, cannot create entries
                                logger.debug('D- Item match multipleResults, ignoring')
                            else:
                                #tvs is ok, call scan on tvs folder
                                self.scanDir(os.path.join(path,item), True, item)
                                logger.debug('D- Item ok, scanning subdirectories')
                                pass
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

                else:
                    logger.debug('Item is a file')
                    if len(existingEp) == 0 and len(forceUpdateEp) == 0 and len(idUpdateEp) == 0:
                        #fill the buffer with episodes that mustn't be updated
                        cursor.execute("SELECT season, episode from episodes WHERE idShow = "+str(tvs[currentTVS]["idShow"])+" AND forceUpdate = 0;")
                        dat = cursor.fetchall()
                        for i in dat:
                            existingEp.append(str(i["season"])+"."+str(i["episode"]))
                        cursor.execute("SELECT season || '.' || episode AS epCode, idEpisode from episodes WHERE idShow = "+str(tvs[currentTVS]["idShow"])+" AND forceUpdate = 1;")
                        dat = cursor.fetchall()
                        for i in dat:
                            forceUpdateEp.append(i["epCode"])
                            idUpdateEp[i["epCode"]] = i["idEpisode"]

                        logger.debug('Existing episodes: '+str(existingEp))
                        logger.debug('Force Update episodes: '+str(forceUpdateEp))
                        logger.debug('ID Update episodes: '+str(idUpdateEp))


                    #it is an episode file
                    logger.debug("this is an episode file")
                    extension = item[item.rfind('.')+1:]
                    logger.debug('The extension for: '+currentTVS+' is: '+extension)

                    if extension in self._supportedFiles and currentTVS:
                        logger.debug('This is a supported file')
                        #create entry for episode
                        season = int(re.findall("(?:s)(\\d+)(?:e)", item)[0])
                        episode = int(re.findall("(?:s\\d+e)(\\d+)(?:\\.)", item)[0])
                        epCode = str(season)+"."+str(episode)

                        logger.debug('The episode code is: '+str(epCode))

                        if epCode not in existingEp or epCode in forceUpdateEp:
                            logger.debug('No entries are available for this episode or it is marked as forceUpdate')
                            
                            if tvs[currentTVS]["scraperName"] == "tvdb":
                                logger.debug('Getting tvdb results')
                                result = self._tvdb.getTVSEp(tvs[currentTVS]["scraperID"],season,episode)
                            else:
                                logger.debug('Getting tbdb results')
                                result = self._tmdb.getTVSEp(tvs[currentTVS]["scraperID"],season,episode)

                            forceUpdate = 0
                            if "desc" not in result or ("desc" in result and result["desc"] == ""):
                                logger.debug('Episode overview not available, setting as future forceUpdate')
                                forceUpdate = 1

                            if epCode not in existingEp:
                                logger.debug('Creating new entry')
                                data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], tvs[currentTVS]["scraperName"], result["id"], item, tvs[currentTVS]["idShow"], forceUpdate)
                                cursor.execute("INSERT INTO episodes (title, overview, icon, season, episode, rating, scraperName, scraperID, path, idShow, forceUpdate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",data)
                                commit = True

                            elif epCode in forceUpdateEp:
                                logger.debug('Updating existing entry (forceUpdate)')
                                data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], tvs[currentTVS]["scraperName"], result["id"], item, tvs[currentTVS]["idShow"], forceUpdate, idUpdateEp[epCode])                        
                                cursor.execute("UPDATE episodes SET title = %s, overview = %s, icon = %s, season = %s, episode = %s, rating = %s, scraperName = %s, scraperID = %s, path = %s, idShow = %s, forceUpdate = %s WHERE idEpisode = %s;")
                                commit = True

                            logger.debug('Updating database with: '+str(data))

                if commit:
                    self._connection.commit()
                    logger.debug(str(cursor.rowcount)+'were affected')
            except Exception as ex:
                logger.error('New indexer exception: '+str(ex))
                
        logger.debug('End of scan (recursive: '+str(recursive)+')')
                