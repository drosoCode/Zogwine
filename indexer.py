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
        print("NEW FUNCTION CALLL #####################################")
        print(path, recursive, currentTVS)
        dirContent = os.listdir(path)
        existingEp = []
        forceUpdateEp = []
        idUpdateEp = {}
        paths, tvs = self.getTVSData()
        cursor = self._connection.cursor(dictionary=True)
        
        for item in dirContent:
            try:
                commit = False
                print("==========================================================")
                print(item)

                if os.path.isdir(os.path.join(path,item)):

                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print(item)
                    if recursive:
                        #it is a season directory
                        print("recursive")
                        self.scanDir(os.path.join(path,item), True, currentTVS)
                    else:
                        #it is a tvs directory

                        if item in paths:
                            print("present in paths")
                            if tvs[item]["forceUpdate"] and tvs[item]["scraperName"] and tvs[item]["scraperID"]:
                                print("force update")
                                #tvs must be updated
                                if tvs[item]["scraperName"] == "tvdb":
                                    result = self._tvdb.getTVS(tvs[item]["scraperID"])
                                else:
                                    result = self._tmdb.getTVS(tvs[item]["scraperID"])
                                data = (result["title"], result["desc"], result["icon"], result["fanart"], result["rating"], result["premiered"], json.dumps(result["genres"]), item, tvs[item]["idShow"])
                                print(data)
                                cursor.execute("UPDATE tv_shows SET title = %s, overview = %s, icon = %s, fanart = %s, rating = %s, premiered = %s, genre = %s, path = %s, forceUpdate = 0, multipleResults = NULL WHERE idShow = %s;", data)
                                commit = True
                            elif tvs[item]["multipleResults"]:
                                #there are multiple matches for scraper, cannot create entries
                                print("multiple results")
                            else:
                                #tvs is ok, call scan on tvs folder
                                self.scanDir(os.path.join(path,item), True, item)
                                pass
                        else:
                            #entries for this tvs doesn't exists, create entry with multipleResults
                            print("create new entry")
                            a = self._tvdb.searchTVS(item)
                            b = self._tmdb.searchTVS(item)
                            if isinstance(a,dict):
                                a = [a]
                            if isinstance(b,dict):
                                b = [b]
                            results = a + b
                            print(results)
                            cursor.execute("INSERT INTO tv_shows (multipleResults, path) VALUES (%s, %s);", (json.dumps(results), item))
                            commit = True

                else:
                    if len(existingEp) == 0 and len(forceUpdateEp) == 0 and len(idUpdateEp) == 0:
                        #fill the buffer with episodes that mustn't be updated
                        print("fill ep arrays")
                        cursor.execute("SELECT season, episode from episodes WHERE idShow = "+str(tvs[currentTVS]["idShow"])+" AND forceUpdate = 0;")
                        dat = cursor.fetchall()
                        for i in dat:
                            print(i)
                            existingEp.append(str(i["season"])+"."+str(i["episode"]))
                        cursor.execute("SELECT season || '.' || episode AS epCode, idEpisode from episodes WHERE idShow = "+str(tvs[currentTVS]["idShow"])+" AND forceUpdate = 1;")
                        dat = cursor.fetchall()
                        for i in dat:
                            forceUpdateEp.append(i["epCode"])
                            idUpdateEp[i["epCode"]] = i["idEpisode"]
                        print(existingEp)
                        print(forceUpdateEp)
                        print(idUpdateEp)


                    #it is an episode file
                    print("this is an episode file")
                    extension = item[item.rfind('.')+1:]
                    print(extension)
                    print(currentTVS)
                    if extension in self._supportedFiles and currentTVS:
                        print("ok")
                        #create entry for episode
                        season = int(re.findall("(?:s)(\\d+)(?:e)", item)[0])
                        episode = int(re.findall("(?:s\\d+e)(\\d+)(?:\\.)", item)[0])
                        epCode = str(season)+"."+str(episode)

                        print(season,episode,epCode, sep="\t")

                        if epCode not in existingEp or epCode in forceUpdateEp:
                            print("ook")
                            if tvs[currentTVS]["scraperName"] == "tvdb":
                                result = self._tvdb.getTVSEp(tvs[currentTVS]["scraperID"],season,episode)
                            else:
                                print(season, episode, tvs[currentTVS]["scraperID"])
                                result = self._tmdb.getTVSEp(tvs[currentTVS]["scraperID"],season,episode)

                            forceUpdate = 0
                            if "desc" not in result or ("desc" in result and result["desc"] == ""):
                                forceUpdate = 1

                            if epCode not in existingEp:
                                print(result)
                                data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], tvs[currentTVS]["scraperName"], result["id"], item, tvs[currentTVS]["idShow"], forceUpdate)
                                cursor.execute("INSERT INTO episodes (title, overview, icon, season, episode, rating, scraperName, scraperID, path, idShow, forceUpdate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",data)
                                commit = True
                                print("Create new entry")
                            elif epCode in forceUpdateEp:
                                data = (result["title"], result["desc"], result["icon"], result["season"], result["episode"], result["rating"], tvs[currentTVS]["scraperName"], result["id"], item, tvs[currentTVS]["idShow"], forceUpdate, idUpdateEp[epCode])                        
                                cursor.execute("UPDATE episodes SET title = %s, overview = %s, icon = %s, season = %s, episode = %s, rating = %s, scraperName = %s, scraperID = %s, path = %s, idShow = %s, forceUpdate = %s WHERE idEpisode = %s;")
                                commit = True
                                print("update entry")
                            print(data)
                if commit:
                    self._connection.commit()
                    print(cursor.rowcount, "was affected")
            except Exception as ex:
                print("###############################################################################################################################################")
                print(ex)
                print("###############################################################################################################################################")

