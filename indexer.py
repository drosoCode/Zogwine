import mysql.connector as sql
import re
import os
import json
import requests
import urllib.parse
"""
connection = sql.connect(host='192.168.1.12',user='kodi',password='kodi',database='mediaController')
cursor = connection.cursor(dictionary=True)
cursor.execute("SELECT * FROM movie_view ORDER BY c00")
"""

def scanDir(self,path):
    dirContent = os.listdir(path)
    supportedFiles = ["mkv","mp4","avi"]
    filesData = []
    for item in dirContent:
        if os.path.isdir(os.path.join(path,item)):
            filesData = filesData+self.scanDir(os.path.join(path,item))
        else:
            extension = item[item.rfind('.')+1:]
            if extension in supportedFiles:
                season = re.findall("(?:s)(\\d+)(?:e)", item)[1]
                episode = re.findall("(?:s\\d+e)(\\d+)(?:\\.)", item)[1]
                

class tvdb:

    def __init__(self, apiKey):
        self._endpoint = "https://api.thetvdb.com"
        token = json.loads(requests.post(self._endpoint+"/login",data=json.dumps({"apikey":apiKey}), headers={"Content-type":"application/json", "Accept": "application/json"}).text)["token"]
        self._headers = {"Accept":"application/json", "Content-type":"application/json", "Accept-Language":"en", "Authorization": "Bearer "+token}

    def searchTVS(self, name):
        return self.fetchAll("/search/series/?name="+urllib.parse.quote(name))

    def getTVS(self, id):
        return self.fetchAll("/series/"+str(id))

    def getTVSEp(self, id, season, episode=None):
        return self.fetchAll("/series"+str(id)+"/episodes/query?airedSeason="+str(season)+"&airedEpisode="+str(episode))

    def fetchAll(self, query):
        next = 1
        data = []
        if next:
            d = requests.post(self._endpoint+query+"&page="+str(next), headers=self._headers).text
            response = json.loads(d)
            next = response["links"]["next"]
            data += response["data"]
        return self.standardize(data)
    
    def standardize(self, data):
        return data

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
        tmp = {}

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
            elif j == "origin_country":
                tmp["country"] = i[j][0]
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
                tmp["date"] = i[j]
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

        return tmp

#tv = tvdb("7dc4ff87e0beda5f0e6b2e7bf2e8fb1d")
#print(tv.searchTVS("sword art online"))


#tm = tmdb("2f20570b213e05761d12b3f530a86213")
#print(tm.searchTVS("sword art online")[1]["id"])
#print(tm.getTVS(45782))
#print(tm.getTVSEp(45782,1,1))