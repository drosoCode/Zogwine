# coding: utf-8
import re
import os
import json
import requests
import urllib.parse
from importlib import import_module
from base64 import b64encode

class movies:

    def __init__(self, logger, dbConnection, apiKeys):
        self._logger = logger
        self._apiKeys = apiKeys
        self._supportedFiles = ["mkv","mp4","avi"]
        self._connection = dbConnection
        self._scrapers = []
        self.importScrapers()
        self._currentMovie = None
        logger.info('Movies Indexer Initialised Successfully')
        logger.info('Supported file formats: '+str(self._supportedFiles))

    def encodeImg(self, img):
        if img is not None and img != "":
            return b64encode(img.encode()).decode()
        else:
            return None

    def importScrapers(self):
        for i in os.listdir('scrapers/'):
            if 'movies_' in i and i[i.rfind('.')+1:] == 'py' and 'main' not in i:
                try:
                    scraperName = i[i.rfind('_')+1:i.rfind('.')]
                    module = import_module('movies_'+scraperName)
                    my_class = getattr(module, scraperName)
                    if my_class.__name__ in self._apiKeys:
                        instance = my_class(self._apiKeys[my_class.__name__])
                        self._scrapers.append(instance)
                        self._logger.info('Scraper '+str(my_class.__name__)+' successfully initialised')
                    else:
                        self._logger.warning('Failed to import scraper '+str(my_class.__name__))
                except:
                    self._logger.warning('Failed to import scraper '+str(my_class.__name__))

    def getName(self, fileName):
        fileName = fileName[fileName.rfind('/')+1:]
        regex = "(?i)^(.+?)[._( \\t]*(?:(19\\d{2}|20(?:0\\d|1[0-9]))|(fansub|VOST|bluray|\\d+p|brrip|webrip|hevc|x26|h26)|(\\[.*\\])|(mkv|avi|mpe?g|mp4)$)"
        find = re.findall(regex, fileName)
        year = -1
        if len(find) > 0 and len(find[0][0]) > 0:
            name = find[0][0]
            if len(find[0][1]) == 4:
                year = find[0][1]
        else:
            name = fileName[:fileName.rfind('.')]
        name = name.replace('_', ' ').replace('.', ' ')

        return (name, year)

    def getMovieData(self):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM movies ORDER BY title;")
        dat = cursor.fetchall()
        paths = []
        movies = {}
        for i in dat:
            paths.append(i["path"])
            movies[i["path"]] = i
        return paths, movies

    def scanDir(self, path, recursive=False, addPath=''):
        self._logger.info('Scan Dir Triggered, recursive: '+str(recursive)+' ; current Movie: '+str(self._currentMovie))
        self._paths, self._movies = self.getMovieData()
        
        for item in os.listdir(path):
            self._logger.debug('New Item: '+str(item))

            if os.path.isdir(os.path.join(path,item)):
                self._logger.debug('Item is a directory')
                self.scanDir(path, True, os.path.join(addPath, item))
            else:
                self._logger.debug('Item is a file')
                self.scanMovie(os.path.join(addPath, item))
                
        self._logger.debug('End of scan (recursive: '+str(recursive)+')')
    

    def scanMovie(self, item):
        cursor = self._connection.cursor(dictionary=True)
        commit = False

        if item in self._paths:
            self._logger.debug('Entries for this item exists in database')

            if self._movies[item]["forceUpdate"] and self._movies[item]["scraperName"] and self._movies[item]["scraperID"]:
                self._logger.debug('Item is marked as force update')
                #movie must be updated
                result = []
                for s in self._scrapers:
                    #create empty dict
                    result = {'title': None,'desc': None, 'icon': None, 'fanart': None, 'premiered': None, 'rating': None, 'scraperData': None}
                    if s.__class__.__name__ == self._movies[item]["scraperName"]:
                        result.update(s.getMovie(self._movies[item]["scraperID"]))
                        break
                data = (result["title"], result["overview"], self.encodeImg(result["icon"]), self.encodeImg(result["fanart"]), result["rating"], result["premiered"], item, self._movies[item]["idMovie"])
                cursor.execute("UPDATE movies SET title = %s, overview = %s, icon = %s, fanart = %s, rating = %s, premiered = %s, path = %s, forceUpdate = 0, multipleResults = NULL WHERE idMovie = %s;", data)
                #update tags and people
                self.scanMovieData(self._movies[item]["scraperName"], self._movies[item]["scraperID"], self._movies[item]["idMovie"])
                
                commit = True

                self._logger.debug('Updating database with: '+str(data))

            elif self._movies[item]["multipleResults"]:
                if self._movies[item]["multipleResults"][0] == '[':
                    #there are multiple matches for scraper, cannot create entries
                    self._logger.debug('Item match multipleResults, ignoring')
                else:
                    #the multipleResults field stores a new "search title"
                    self._logger.debug('New search')
                    results = []
                    for s in self._scrapers:
                        data = s.searchMovie(self._movies[item]["multipleResults"])
                        if isinstance(data, dict):
                            data = [data]
                        results += data
                    self._logger.debug('The multipleResults are: '+str(results))
                    cursor.execute("UPDATE movies SET multipleResults = %(mR)s WHERE idMovie = %(idMovie)s;", {'mR': json.dumps(results), 'idMovie': self._movies[item]["idMovie"]})
                    commit = True
        else:
            #entries for this tvs doesn't exists, create entry with multipleResults
            self._logger.debug('Entries for this item doesn\'t exists in database')

            if item[item.rfind('.')+1:] in self._supportedFiles:
                results = []
                for s in self._scrapers:
                    data = s.searchMovie(*self.getName(item))
                    if isinstance(data, dict):
                        data = [data]
                    results += data

                self._logger.debug('The multipleResults are: '+str(results))
                cursor.execute("INSERT INTO movies (multipleResults, path) VALUES (%s, %s);", (json.dumps(results), item))
                commit = True

        if commit:
            self._connection.commit()
            self._logger.debug(str(cursor.rowcount)+'were affected')

    def scanMovieData(self, scraperName, scraperID, idMovie):
        cursor = self._connection.cursor(dictionary=True)
        #scan tags and persons for a movie
        for s in self._scrapers:
            if s.__class__.__name__ == scraperName:
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

                #get existing tags for this movie
                cursor.execute("SELECT idTag FROM tags_link WHERE mediaType = 3 AND idMedia = %(idMovie)s;", {'idMovie': idMovie})
                existingTags = []
                for i in cursor.fetchall():
                    existingTags.append(i['idTag'])
                #link new tags to this movie
                for i in newTags:
                    if i not in existingTags:
                        cursor.execute("INSERT INTO tags_link (idTag, idMedia, mediaType) VALUES (%(idTag)s, %(idMovie)s, 3);", {'idTag': i, 'idMovie': idMovie})
                        commit = True
                        
                #persons part
                movPersonsIDs = []
                movPersons = s.getPersons(scraperID)
                for p in movPersons:
                    cursor.execute("SELECT idPers FROM persons WHERE name = %(name)s;", {'name': p[0]})
                    idPers = cursor.fetchone()
                    if idPers == None:
                        #create person if new
                        cursor.execute("INSERT INTO persons (name) VALUES (%(name)s);", {'name': p[0]})
                        #get person id
                        cursor.execute("SELECT idPers FROM persons WHERE name = %(name)s;", {'name': p[0]})
                        idPers = cursor.fetchone()
                        commit = True
                    movPersonsIDs.append(idPers['idPers'])
                
                #get existing persons for this tvs
                cursor.execute("SELECT idPers FROM persons_link WHERE mediaType = 3 AND idMedia = %(idMovie)s;", {'idMovie': idMovie})
                existingPers = []
                for i in cursor.fetchall():
                    existingPers.append(i['idPers'])
                #link new tags to this tv_show
                for i in range(len(movPersonsIDs)):
                    if movPersonsIDs[i] not in existingPers:
                        cursor.execute("INSERT INTO persons_link (idPers, idMedia, mediaType, role) VALUES (%(idPers)s, %(idMovie)s, 3, %(role)s);", {'idPers': movPersonsIDs[i], 'idMovie': idMovie, 'role': movPersons[i][1]})

        return True
