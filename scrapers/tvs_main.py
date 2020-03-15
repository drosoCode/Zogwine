# coding: utf-8
import re
import os
import json
import requests
import urllib.parse
from importlib import import_module

class tvs:

    def __init__(self, logger, dbConnection, apiKeys):
        self._logger = logger
        self._apiKeys = apiKeys
        self._supportedFiles = ["mkv","mp4","avi"]
        self._connection = dbConnection
        self._scrapers = []
        self.importScrapers()
        self._currentTVS = None
        logger.info('TVS Indexer Initialised Successfully')
        logger.info('Supported file formats: '+str(self._supportedFiles))

    def importScrapers(self):
        for i in os.listdir('scrapers/'):
            if 'tvs_' in i and i[i.rfind('.')+1:] == 'py' and 'main' not in i:
                scraperName = i[i.rfind('_')+1:i.rfind('.')]
                module = import_module('tvs_'+scraperName)
                my_class = getattr(module, scraperName)
                if my_class.__name__ in self._apiKeys:
                    instance = my_class(self._apiKeys[my_class.__name__])
                    self._scrapers.append(instance)
                    self._logger.info('Scraper '+str(my_class.__name__)+' successfully initialised')
                else:
                    self._logger.warning('Failed to import scraper '+str(my_class.__name__))

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
        self._logger.info('Scan Dir Triggered, recursive: '+str(recursive)+' ; current TVS: '+str(self._currentTVS)+' ; additionnalPath: '+addPath)
        dirContent = os.listdir(path)
        self._existingEp = []
        self._forceUpdateEp = []
        self._idUpdateEp = {}
        self._paths, self._tvs = self.getTVSData()
        cursor = self._connection.cursor(dictionary=True)
        
        for item in dirContent:
            #try:
                commit = False
                self._logger.debug('New Item: '+str(item))

                if os.path.isdir(os.path.join(path,item)):
                    self._logger.debug('Item is a directory')
                    
                    if recursive:
                        #we are inside a tvs dir, so it is a season directory
                        self._logger.debug('D- It is a season directory (recursive call)')
                        if addPath != '':
                            newAddPath = addPath + '/' + item
                        else:
                            newAddPath = item
                        self._logger.debug('Path inside tvs directory: '+str(newAddPath))
                        self.scanDir(os.path.join(path,item), True, newAddPath)
                    else:
                        #it is a tvs directory
                        self._logger.debug('D- It is a TVS root directory')
                        self.scanTVS(path, item)
                        
                else:
                    self._logger.debug('Item is a file')
                    if len(self._existingEp) == 0 and len(self._forceUpdateEp) == 0 and len(self._idUpdateEp) == 0:
                        #fill the buffer with episodes that mustn't be updated
                        cursor.execute("SELECT CONCAT(season,'.',episode) AS epCode, idEpisode, forceUpdate from episodes WHERE idShow = "+str(self._tvs[self._currentTVS]["idShow"])+";")
                        dat = cursor.fetchall()
                        for i in dat:
                            self._existingEp.append(i["epCode"])
                            if i['forceUpdate']:
                                self._forceUpdateEp.append(i["epCode"])
                                self._idUpdateEp[i["epCode"]] = i["idEpisode"]

                        self._logger.debug('Existing episodes: '+str(self._existingEp))
                        self._logger.debug('Force Update episodes: '+str(self._forceUpdateEp))
                        self._logger.debug('ID Update episodes: '+str(self._idUpdateEp))

                    #it is an episode file
                    self._logger.debug("this is an episode file")
                    self.scanEpisode(addPath,item)

                if commit:
                    self._connection.commit()
                    self._logger.debug(str(cursor.rowcount)+' rows affected')
            #except Exception as ex:
            #    self._logger.error('New indexer exception: '+str(ex))
                
        self._logger.debug('End of scan (recursive: '+str(recursive)+')')
    

    def scanTVS(self, path, item):
        cursor = self._connection.cursor(dictionary=True)
        commit = False

        if item in self._paths:
            self._logger.debug('D- Entries for this item exists in database')

            if self._tvs[item]["forceUpdate"] and self._tvs[item]["scraperName"] and self._tvs[item]["scraperID"]:
                self._logger.debug('D- Item is marked as force update')
                #tvs must be updated
                result = []
                for s in self._scrapers:
                    #create empty dict
                    result = {'title': None,'desc': None, 'icon': None, 'fanart': None, 'premiered': None, 'rating': None,'genres': None}
                    
                    if s.__class__.__name__ == self._tvs[item]["scraperName"]:
                        result.update(s.getTVS(self._tvs[item]["scraperID"]))

                data = (result["title"], result["desc"], result["icon"], result["fanart"], result["rating"], result["premiered"], json.dumps(result["genres"]), item, self._tvs[item]["idShow"])
                cursor.execute("UPDATE tv_shows SET title = %s, overview = %s, icon = %s, fanart = %s, rating = %s, premiered = %s, genre = %s, path = %s, forceUpdate = 0, multipleResults = NULL WHERE idShow = %s;", data)
                commit = True

                self._logger.debug('Updating database with: '+str(data))

            elif self._tvs[item]["multipleResults"]:
                #there are multiple matches for scraper, cannot create entries
                self._logger.debug('D- Item match multipleResults, ignoring')
            else:
                #tvs is ok, call scan on tvs folder
                self._currentTVS = item
                self.scanDir(os.path.join(path,item), True)
                self._logger.debug('D- Item ok, scanning subdirectories')
        else:
            #entries for this tvs doesn't exists, create entry with multipleResults
            self._logger.debug('Entries for this item doesn\'t exists in database')

            results = []
            for s in self._scrapers:
                data = s.searchTVS(item)
                if isinstance(data, dict):
                    data = [data]
                results += data

            self._logger.debug('The multipleResults are: '+str(results))
            cursor.execute("INSERT INTO tv_shows (multipleResults, path) VALUES (%s, %s);", (json.dumps(results), item))
            commit = True

        if commit:
            self._connection.commit()
            self._logger.debug(str(cursor.rowcount)+'were affected')


    def scanEpisode(self, path, item):
        extension = item[item.rfind('.')+1:]
        self._logger.debug('The extension for: '+self._currentTVS+' is: '+extension)
        cursor = self._connection.cursor(dictionary=True)
        commit = False

        if extension in self._supportedFiles and self._currentTVS:
            self._logger.debug('This is a supported file')
            #create entry for episode
            season = re.findall("(?i)(?:s)(\\d+)(?:e)", item)
            episode = re.findall("(?i)(?:s\\d+e)(\\d+)(?:\\.)", item)
            if len(season) > 0 and len(episode) > 0:
                season = int(season[0])
                episode = int(episode[0])
                epCode = str(season)+"."+str(episode)

                self._logger.debug('The episode code is: '+str(epCode))

                if epCode not in self._existingEp or epCode in self._forceUpdateEp:
                    self._logger.debug('No entries are available for this episode or it is marked as forceUpdate')
                    #create empty dict
                    result = {'title': None,'desc': None, 'icon': None, 'season': None, 'episode': None, 'rating': None,'id': None}
                    
                    for s in self._scrapers:
                        if s.__class__.__name__ == self._tvs[self._currentTVS]["scraperName"]:
                            self._logger.debug('Getting '+str(s.__class__.__name__)+' results')
                            result.update(s.getTVSEp(self._tvs[self._currentTVS]["scraperID"],season,episode))
                            break

                    forceUpdate = 0
                    if "desc" not in result or ("desc" in result and result["desc"] == ""):
                        self._logger.debug('Episode overview not available, setting as future forceUpdate')
                        forceUpdate = 1

                    if result['id'] != None:
                        if path != '':
                            filePath = path + '/' + item
                        else:
                            filePath = item

                        if epCode not in self._existingEp:
                            self._logger.debug('Creating new entry')
                            data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], self._tvs[self._currentTVS]["scraperName"], result["id"], filePath, self._tvs[self._currentTVS]["idShow"], forceUpdate)
                            cursor.execute("INSERT INTO episodes (title, overview, icon, season, episode, rating, scraperName, scraperID, path, idShow, forceUpdate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",data)
                            commit = True

                        elif epCode in self._forceUpdateEp:
                            self._logger.debug('Updating existing entry (forceUpdate)')
                            data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], self._tvs[self._currentTVS]["scraperName"], result["id"], filePath, self._tvs[self._currentTVS]["idShow"], forceUpdate, self._idUpdateEp[epCode])                        
                            cursor.execute("UPDATE episodes SET title = %s, overview = %s, icon = %s, season = %s, episode = %s, rating = %s, scraperName = %s, scraperID = %s, path = %s, idShow = %s, forceUpdate = %s WHERE idEpisode = %s;", data)
                            commit = True

                        self._logger.debug('Updating database with: '+str(data))
                    else:
                        self._logger.warning('Episode ID is null') 
                else:
                    self._logger.debug('Entries for this episode already exists') 
            else:
                self._logger.warning('Cannot extract season or episode from file name')

        if commit:
            self._connection.commit()
            self._logger.debug(str(cursor.rowcount)+'were affected')