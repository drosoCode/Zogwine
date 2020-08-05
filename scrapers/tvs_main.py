# coding: utf-8
import re
import os
import json
import requests
import urllib.parse
from importlib import import_module
from base64 import b64encode

class tvs:

    def __init__(self, logger, dbConnection, apiKeys):
        self._logger = logger
        self._apiKeys = apiKeys
        self._supportedFiles = ["mkv","mp4","avi"]
        self._connection = dbConnection
        self._scrapers = []
        self.importScrapers()
        self._currentTVS = None
        self._seasons = []
        logger.info('TVS Indexer Initialised Successfully')
        logger.info('Supported file formats: '+str(self._supportedFiles))

    def encodeImg(self, img):
        if img is not None and img != "":
            return b64encode(img.encode()).decode()
        else:
            return None

    def importScrapers(self):
        for i in os.listdir('scrapers/'):
            if 'tvs_' in i and i[i.rfind('.')+1:] == 'py' and 'main' not in i:
                try:
                    scraperName = i[i.rfind('_')+1:i.rfind('.')]
                    module = import_module('tvs_'+scraperName)
                    my_class = getattr(module, scraperName)
                    if my_class.__name__ in self._apiKeys:
                        instance = my_class(self._apiKeys[my_class.__name__])
                        self._scrapers.append(instance)
                        self._logger.info('Scraper '+str(my_class.__name__)+' successfully initialised')
                    else:
                        self._logger.warning('Failed to import scraper '+str(my_class.__name__))
                except:
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
                    result = {'title': None,'overview': None, 'icon': None, 'fanart': None, 'premiered': None, 'rating': None,'genres': None, 'scraperData': None}
                    if s.__class__.__name__ == self._tvs[item]["scraperName"]:
                        result.update(s.getTVS(self._tvs[item]["scraperID"]))
                        break
                data = (result["title"], result["overview"], self.encodeImg(result["icon"]), self.encodeImg(result["fanart"]), result["rating"], result["premiered"], json.dumps(result["genres"]), item, self._tvs[item]["idShow"])
                cursor.execute("UPDATE tv_shows SET title = %s, overview = %s, icon = %s, fanart = %s, rating = %s, premiered = %s, genre = %s, path = %s, forceUpdate = 0, multipleResults = NULL WHERE idShow = %s;", data)
                commit = True

                self._logger.debug('Updating database with: '+str(data))

            elif self._tvs[item]["multipleResults"]:
                #there are multiple matches for scraper, cannot create entries
                self._logger.debug('D- Item match multipleResults, ignoring')
            else:
                #tvs is ok, call scan on tvs folder
                self._seasons = []
                self._currentTVS = item
                #scan for subfolders/files
                self.scanDir(os.path.join(path,item), True)
                #scan for seasons
                if self.scanSeasons():
                    commit = True
                #scan for tags and people
                if self.scanShowData():
                    commit = True
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
                if season not in self._seasons:
                    self._seasons.append(season)
                episode = int(episode[0])
                epCode = str(season)+"."+str(episode)

                self._logger.debug('The episode code is: '+str(epCode))

                if epCode not in self._existingEp or epCode in self._forceUpdateEp:
                    self._logger.debug('No entries are available for this episode or it is marked as forceUpdate')
                    #create empty dict
                    result = {'title': item,'overview': None, 'icon': None, 'season': season, 'episode': episode, 'rating': None,'id': None}
                    
                    for s in self._scrapers:
                        if s.__class__.__name__ == self._tvs[self._currentTVS]["scraperName"]:
                            self._logger.debug('Getting '+str(s.__class__.__name__)+' results')
                            result.update(s.getTVSEp(self._tvs[self._currentTVS]["scraperID"], season, episode, self._tvs[self._currentTVS]["scraperData"]))
                            break

                    forceUpdate = 0
                    if "overview" not in result or ("overview" in result and result["overview"] == ""):
                        self._logger.debug('Episode overview not available, setting as future forceUpdate')
                        forceUpdate = 1

                    if result['id'] == None:
                        self._logger.warning('Episode ID is null')
                        
                    if path != '':
                        filePath = path + '/' + item
                    else:
                        filePath = item

                    if epCode not in self._existingEp:
                        self._logger.debug('Creating new entry')
                        data = (result["title"], result["overview"], self.encodeImg(result["icon"]), result["season"], result["episode"], result["rating"], self._tvs[self._currentTVS]["scraperName"], result["id"], filePath, self._tvs[self._currentTVS]["idShow"], forceUpdate)
                        cursor.execute("INSERT INTO episodes (title, overview, icon, season, episode, rating, scraperName, scraperID, path, idShow, forceUpdate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",data)
                        commit = True

                    elif epCode in self._forceUpdateEp:
                        self._logger.debug('Updating existing entry (forceUpdate)')
                        data = (result["title"], result["overview"], self.encodeImg(result["icon"]), result["season"], result["episode"], result["rating"], self._tvs[self._currentTVS]["scraperName"], result["id"], filePath, self._tvs[self._currentTVS]["idShow"], forceUpdate, self._idUpdateEp[epCode])                        
                        cursor.execute("UPDATE episodes SET title = %s, overview = %s, icon = %s, season = %s, episode = %s, rating = %s, scraperName = %s, scraperID = %s, path = %s, idShow = %s, forceUpdate = %s WHERE idEpisode = %s;", data)
                        commit = True

                    self._logger.debug('Updating database with: '+str(data)) 
                else:
                    self._logger.debug('Entries for this episode already exists') 
            else:
                self._logger.warning('Cannot extract season or episode from file name')

        if commit:
            self._connection.commit()
            self._logger.debug(str(cursor.rowcount)+'were affected')

    def scanSeasons(self):
        #scan seasons for a tv_show
        commit = False
        scraperID = self._tvs[self._currentTVS]["scraperID"]
        idShow = self._tvs[self._currentTVS]["idShow"]
        cursor = self._connection.cursor(dictionary=True)
        noUpdate = []
        existingSeasons = []
        cursor.execute("SELECT season, forceUpdate FROM seasons WHERE idShow = %(idShow)s;", {'idShow': idShow})
        for s in cursor.fetchall():
            existingSeasons.append(s['season'])
            if s['forceUpdate'] != 1:
                noUpdate.append(s['season'])
        print('SEASONS ===============================================================================')
        for s in self._scrapers:
            if s.__class__.__name__ == self._tvs[self._currentTVS]["scraperName"]:
                self._logger.debug('Getting '+str(s.__class__.__name__)+' results')
                for season in self._seasons:
                    if season not in existingSeasons:
                        #season don't already exists, and must be created
                        data = s.getTVSSeason(scraperID, season)
                        queryData = {'idShow': idShow, 'title': data['title'], 'overview': data['overview'], 'icon': self.encodeImg(data['icon']), 'premiered': data['premiered'], 'forceUpdate': 0, 'season': season}
                        cursor.execute("INSERT INTO seasons (idShow, title, icon, season, premiered, overview, forceUpdate) VALUES (%(idShow)s, %(title)s, %(icon)s, %(season)s, %(premiered)s, %(overview)s, %(forceUpdate)s);", queryData)
                        commit = True
                    elif season not in noUpdate:
                        #season already exists and must be updated
                        data = s.getTVSSeason(scraperID, season)
                        queryData = {'idShow': idShow, 'title': data['title'], 'overview': data['overview'], 'icon': self.encodeImg(data['icon']), 'premiered': data['premiered'], 'forceUpdate': 0}
                        cursor.execute("UPDATE seasons SET title = %(title)s, icon = %(icon)s, season = %(season)s, premiered  = %(premiered)s, overview = %(overview)s, forceUpdate = %(forceUpdate)s WHERE idShow = %(idShow)s;", queryData)
                        commit = True
                break
        return commit

    def scanShowData(self):
        #scan tags and persons for a tv_show
        commit = False
        scraperID = self._tvs[self._currentTVS]["scraperID"]
        idShow = self._tvs[self._currentTVS]["idShow"]
        cursor = self._connection.cursor(dictionary=True)

        for s in self._scrapers:
            if s.__class__.__name__ == self._tvs[self._currentTVS]["scraperName"]:
                self._logger.debug('Getting '+str(s.__class__.__name__)+' results')

                #tags part
                newTags = []
                for t in s.getTags(scraperID):
                    cursor.execute("SELECT idTag FROM tags where name = %(name)s AND value = %(value)s;", {'name': t[0], 'value': t[1]})
                    idTag = cursor.fetchone()
                    if idTag == None:
                        #create tag if new
                        cursor.execute("INSERT INTO tags (name, value, icon) VALUES (%(name)s, %(value)s, %(icon)s);", {'name': t[0], 'value': t[1], 'icon': self.encodeImg(t[2])})
                        #get tag id
                        cursor.execute("SELECT idTag FROM tags where name = %(name)s AND value = %(value)s;", {'name': t[0], 'value': t[1]})
                        idTag = cursor.fetchone()
                        commit = True
                    newTags.append(idTag['idTag'])

                #get existing tags for this tvs
                cursor.execute("SELECT idTag FROM tags_link WHERE mediaType = 2 AND idMedia = %(idShow)s;", {'idShow': idShow})
                existingTags = []
                for i in cursor.fetchall():
                    existingTags.append(i['idTag'])
                #link new tags to this tv_show
                for i in newTags:
                    if i not in existingTags:
                        cursor.execute("INSERT INTO tags_link (idTag, idMedia, mediaType) VALUES (%(idTag)s, %(idShow)s, 2);", {'idTag': i, 'idShow': idShow})
                        commit = True
                        
                #persons part
                tvsPersons = s.getPersons(scraperID)
                tvsPersonsIDs = []
                for p in tvsPersons:
                    cursor.execute("SELECT idPers FROM persons WHERE name = %(name)s;", {'name': p[0]})
                    idPers = cursor.fetchone()
                    if idPers == None:
                        #create person if new
                        cursor.execute("INSERT INTO persons (name) VALUES (%(name)s);", {'name': p[0]})
                        #get person id
                        cursor.execute("SELECT idPers FROM persons WHERE name = %(name)s;", {'name': p[0]})
                        idPers = cursor.fetchone()
                        commit = True
                    tvsPersonsIDs.append(idPers['idPers'])
                
                #get existing persons for this tvs
                cursor.execute("SELECT idPers FROM persons_link WHERE mediaType = 2 AND idMedia = %(idShow)s;", {'idShow': idShow})
                existingPers = []
                for i in cursor.fetchall():
                    existingPers.append(i['idPers'])
                #link new tags to this tv_show
                for i in range(len(tvsPersonsIDs)):
                    if tvsPersonsIDs[i] not in existingPers:
                        cursor.execute("INSERT INTO persons_link (idPers, idMedia, mediaType, role) VALUES (%(idPers)s, %(idShow)s, 2, %(role)s);", {'idPers': tvsPersonsIDs[i], 'idShow': idShow, 'role': tvsPersons[i][1]})

        return commit

    def scanUpcomingEpisodes(self):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute('DELETE FROM upcoming_episodes WHERE date < DATE(SYSDATE())')
        cursor.execute("SELECT idShow, scraperName, scraperID " \
                       "FROM tv_shows "\
                       "WHERE multipleResults IS NULL AND idShow NOT IN (SELECT idShow FROM upcoming_episodes)")
        for tvs in cursor.fetchall():
            for s in self._scrapers:
                if s.__class__.__name__ == tvs['scraperName']:
                    self._logger.info('Getting '+str(s.__class__.__name__)+' results')
                    ep = s.getUpcomingEpisode(tvs['scraperID'])
                    if ep is not None:
                        queryData = {'title': ep.get('title'), 'overview': ep.get('overview'), 'season': ep.get('season'), 'episode': ep.get('episode'), 'date': ep.get('date'), 'icon': ep.get('icon'), 'idShow': tvs['idShow']}
                        cursor.execute("INSERT INTO upcoming_episodes (title, overview, season, episode, date, icon, idShow) "\
                                    "VALUES (%(title)s, %(overview)s, %(season)s, %(episode)s, %(date)s, %(icon)s, %(idShow)s)", queryData)
        
        self._connection.commit()
        self._logger.debug(str(cursor.rowcount)+'were affected')
