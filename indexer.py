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

def run(configFile):
    with open(configFile) as f:
        data = json.load(f)
        s = scanner(data["db"]["host"],data["db"]["user"], data["db"]["password"], data["api"]["tmdb"], data["api"]["tvdb"])
        s.scanDir("W:\\Videos\\Series")

class scanner:

    def __init__(self, host, user, passw, tmdbKey, tvdbKey):
        self._supportedFiles = ["mkv","mp4","avi"]
        self._connection = sql.connect(host=host,user=user,password=passw,database='mediaController')
        self._tvdb = tvdb(tvdbKey)
        self._tmdb = tmdb(tmdbKey)

    def getTVSData(self):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tv_shows ORDER BY title")
        dat = cursor.fetchall()
        paths = []
        tvs = {}
        for i in dat:
            paths.append(i["path"])
            tvs[i["path"]] = i
        return paths, tvs

    def scanDir(self,path, recursive=False):
        dirContent = os.listdir(path)
        filesData = []
        currentTVS = None
        doNotUpdateEp = []
        paths, tvs = self.getTVSData()
        
        for item in dirContent:
            if os.path.isdir(os.path.join(path,item)):
                currentTVS = None
                doNotUpdateEp = []

                if recursive:
                    #it is a season directory
                    self.scanDir(os.path.join(path,item), True)
                else:
                    #it is a tvs directory
                    if item in paths:
                        currentTVS = item
                        if tvs[item]["multipleResults"]:
                            #there are multiple matches for scraper, cannot create entries
                            pass
                        elif tvs[item]["forceUpdate"]:
                            #tvs must be updated
                        else:
                            #tvs is ok, fill the buffer with episodes that mustn't be updated
                    else:
                        #entries for this tvs doesn't exists, create entry with multipleResults

            else:
                #it is an episode file
                extension = item[item.rfind('.')+1:]
                if extension in self._supportedFiles and currentTVS:
                    #create entry for 
                    season = re.findall("(?:s)(\\d+)(?:e)", item)[1]
                    episode = re.findall("(?:s\\d+e)(\\d+)(?:\\.)", item)[1]
                    #tvs[currentTVS]["scraperName"]
                    #tvs[currentTVS]["scraperID"]


class tvdb:

    def __init__(self, apiKey):
        self._endpoint = "https://api.thetvdb.com"
        token = json.loads(requests.post(self._endpoint+"/login",data=json.dumps({"apikey":apiKey}), headers={"Content-type":"application/json", "Accept": "application/json"}).text)["token"]
        self._headers = {"Accept":"application/json", "Content-type":"application/json", "Accept-Language":"en", "Authorization": "Bearer "+token}

    def searchTVS(self, name):
        return self.standardize(json.loads(requests.get(self._endpoint+"/search/series?name="+urllib.parse.quote(name), headers=self._headers).text)["data"])

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
