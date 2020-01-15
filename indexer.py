import mysql.connector as sql
import re
import os
import json
import requests
import urllib.parse


#print(tv.searchTVS("sword art online")[1])
#print(tv.getTVS(259640))
#print(tv.getTVSEp(259640,1,1))


#print(tm.searchTVS("sword art online")[1])
#print(tm.getTVS(45782))
#print(tm.getTVSEp(45782,1,1))


class scanner:

    def __init__(self, host, user, passw, tmdbKey, tvdbKey):
        self._supportedFiles = ["mkv","mp4","avi"]
        self._connection = sql.connect(host=host,user=user,password=passw,database='mediaController')
        self._tvdb = tvdb(tvdbKey)
        self._tmdb = tmdb(tmdbKey)

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
                        if tvs[item]["multipleResults"]:
                            #there are multiple matches for scraper, cannot create entries
                            print("multiple results")
                        elif tvs[item]["forceUpdate"]:
                            print("force update")
                            #tvs must be updated
                            if tvs[item]["scraperName"] == "tvdb":
                                result = self._tvdb.getTVS(tvs[item]["scraperID"])
                            else:
                                result = self._tmdb.getTVS(tvs[item]["scraperID"])
                            data = (result["title"], result["desc"], result["icon"], result["fanart"], result["rating"], result["premiered"], json.dumps(result["genres"]), item, tvs[item]["idShow"])
                            print(data)
                            cursor.execute("UPDATE tv_shows SET title = %s, overview = %s, icon = %s, fanart = %s, rating = %s, premiered = %s, genre = %s, path = %s, forceUpdate = 0 WHERE idShow = %s;", data)
                            commit = True
                        else:
                            #tvs is ok, call scan on tvs folder
                            self.scanDir(os.path.join(path,item), True, item)
                    else:
                        #entries for this tvs doesn't exists, create entry with multipleResults
                        print("create new entry")
                        results = self._tvdb.searchTVS(item) + self._tmdb.searchTVS(item)
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

class tvdb:

    def __init__(self, apiKey):
        self._endpoint = "https://api.thetvdb.com"
        token = json.loads(requests.post(self._endpoint+"/login",data=json.dumps({"apikey":apiKey}), headers={"Content-type":"application/json", "Accept": "application/json"}).text)["token"]
        self._headers = {"Accept":"application/json", "Content-type":"application/json", "Accept-Language":"en", "Authorization": "Bearer "+token}

    def searchTVS(self, name):
        d = json.loads(requests.get(self._endpoint+"/search/series?name="+urllib.parse.quote(name), headers=self._headers).text)
        if "Error" in d:
            return []
        else:
            return self.standardize(d["data"])

    def getTVS(self, id):
        return self.standardize(json.loads(requests.get(self._endpoint+"/series/"+str(id), headers=self._headers).text)["data"])

    def getTVSEp(self, id, season, episode=None):
        return self.standardize(json.loads(requests.get(self._endpoint+"/series/"+str(id)+"/episodes/query?airedSeason="+str(season)+"&airedEpisode="+str(episode), headers=self._headers).text)["data"])

    def standardize(self, data):
        if isinstance(data, list):
            dat = []
            for i in data:
                dat.append(self.subStandardize(i))
            return dat
        else:
            return self.subStandardize(data)

    def subStandardize(self, i):
        tmp = {"scraperName":"tvdb"}
        baseImgUrl = "https://artworks.thetvdb.com"
        baseImgUrl2 = "https://artworks.thetvdb.com/banners/"

        for j in i.keys():
            if j == "vote_average":
                tmp["rating"] = i[j]
            elif j == "firstAired":
                tmp["premiered"] = i[j]
            elif j == "banner" and i[j][0] == "/":
                if i[j] != None:
                    tmp["icon"] = baseImgUrl + i[j]
                else:
                    tmp["icon"] = None
            elif j == "poster":
                if i[j] != None:
                    tmp["icon"] = baseImgUrl2 + i[j]
                else:
                    tmp["icon"] = None                
            elif j == "fanart":
                if i[j] != None:
                    tmp["fanart"] = baseImgUrl2 + i[j]
                else:
                    tmp["fanart"] = None
            elif j == "seriesName":
                tmp["title"] = i[j]
            elif j == "overview":
                tmp["desc"] = i[j]
            elif j == "id":
                tmp["id"] = i[j]
            elif j == "status":
                if i[j] == "Continuing":
                    tmp["in_production"] = True
                else:
                    tmp["in_production"] = False
            elif j == "airedSeason":
                tmp["season"] = i[j]
            elif j == "airedEpisodeNumber":
                tmp["episode"] = i[j]
            elif j == "genre":
                tmp["genres"] = i[j]
            elif j == "episodeName":
                tmp["title"] = i[j]
            elif j == "filename":
                if i[j] != None:
                    tmp["icon"] = baseImgUrl2 + i[j]
                else:
                    tmp["icon"] = None
            elif j == "siteRating":
                tmp["rating"] = i[j]

        return tmp

class tmdb:

    def __init__(self, apikey):
        self._endpoint = "https://api.themoviedb.org/3/"
        self._apikey = apikey

    def getTVS(self, id):
        return self.standardize(json.loads(requests.get(self._endpoint+"tv/"+str(id)+"?api_key="+self._apikey).text))

    def getTVSEp(self, id, season, episode):
        return self.standardize(json.loads(requests.get(self._endpoint+"tv/"+str(id)+"/season/"+str(season)+"/episode/"+str(episode)+"?api_key="+self._apikey).text))

    def searchTVS(self, name):
        next = 1
        data = []
        while next:
            response = json.loads(requests.get(self._endpoint+"search/tv?query="+urllib.parse.quote(name)+"&api_key="+self._apikey+"&page="+str(next)).text)
            if response["page"] < response["total_pages"]:
                next += 1
            else:
                next = None
            data += response["results"]
        return self.standardize(data)

    def standardize(self, data):
        if isinstance(data, list):
            dat = []
            for i in data:
                dat.append(self.subStandardize(i))
            return dat
        else:
            return self.subStandardize(data)

    def subStandardize(self, i):
        baseImgUrl = "http://image.tmdb.org/t/p/w500"
        genres = {"28":"Action", "12":"Adventure", "16":"Animation", "35":"Comedy", "80":"Crime", "99":"Documentary", "18":"Drama", "10751":"Family", "14":"Fantasy", "36":"History", "27":"Horror", "10402":"Music", "9648":"Mystery", "10749":"Romance", "878":"Science Fiction", "10770":"TV Movie", "53":"Thriller", "10752":"War", "37":"Western"}
        tmp = {"scraperName":"tmdb"}

        for j in i.keys():
            if j == "vote_average":
                tmp["rating"] = i[j]
            elif j == "first_air_date":
                tmp["premiered"] = i[j]
            elif j == "backdrop_path":
                if i[j] != None:
                    tmp["fanart"] = baseImgUrl + i[j]
                else:
                    tmp["fanart"] = None
            elif j == "poster_path":
                if i[j] != None:
                    tmp["icon"] = baseImgUrl + i[j]
                else:
                    tmp["icon"] = None
            elif j == "name":
                tmp["title"] = i[j]
            elif j == "overview":
                tmp["desc"] = i[j]
            elif j == "id":
                tmp["id"] = i[j]
            elif j == "genre_ids":
                tmp["genres"] = []
                for k in i[j]:
                    if str(k) in genres:
                        tmp["genres"].append(genres[str(k)])
            elif j == "genres":
                tmp["genres"] = []
                for k in i[j]:
                    tmp["genres"].append(k["name"])
            elif j == "in_production":
                tmp["in_production"] = i[j]
            elif j == "episode_number":
                tmp["episode"] = i[j]
            elif j == "air_date":
                tmp["premiered"] = i[j]
            elif j == "season_number":
                tmp["season"] = i[j]
            elif j == "seasons":
                seasons = 0
                tmp["specials"] = False
                for k in i[j]:
                    if k["season_number"]  == 0:
                        tmp["specials"] = True
                    else:
                        seasons += 1
                tmp["seasons"] = seasons
            elif j == "still_path":
                if i[j] != None:
                    tmp["icon"] = baseImgUrl + i[j]
                else:
                    tmp["icon"] = None

        return tmp

def run(configFile):
    with open(configFile) as f:
        data = json.load(f)
        s = scanner(data["db"]["host"],data["db"]["user"], data["db"]["password"], data["api"]["tmdb"], data["api"]["tvdb"])
        s.scanDir("W:\\Videos\\Series")

run("config.json")