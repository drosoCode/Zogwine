# coding: utf-8
import requests
import json
import urllib.parse

class tmdb:

    def __init__(self, apikey):
        self._endpoint = "https://api.themoviedb.org/3/"
        self._apikey = apikey
        self._cache = (None, None, None)

    def getTVS(self, id):
        return self.standardize(json.loads(requests.get(self._endpoint+"tv/"+str(id)+"?api_key="+self._apikey).text))

    def getTVSEp(self, id, season, episode, scraperData=None):
        if scraperData == None:
            return self.standardize(json.loads(requests.get(self._endpoint+"tv/"+str(id)+"/season/"+str(season)+"/episode/"+str(episode)+"?api_key="+self._apikey).text))
        else:
            if self._cache[0] != id or self._cache[1] != scraperData:
                self._cache = (id, scraperData, json.loads(requests.get(self._endpoint+"tv/episode_group/"+str(scraperData)+"?api_key="+self._apikey).text))
            resp = self._cache[2]["groups"]
            if len(resp) > 0 and 0 <= season-1 < len(resp) and 0 <= episode-1 < len(resp[season-1]["episodes"]):
                d = resp[season-1]["episodes"][episode-1]
                d["season_number"] = str(season)
                d["episode_number"] = str(episode)
                return self.standardize(d)
            else:
                return self.standardize({})

    #DELETE FROM episodes WHERE idShow = 139;
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
        #check if there is episode groups availables
        i = 0
        d = len(data)
        while i < d:
            res = data[i]
            epGroup = json.loads(requests.get(self._endpoint+"tv/"+str(res["id"])+"/episode_groups?api_key="+self._apikey).text)["results"]
            for eg in epGroup:
                r = res.copy()
                r["name"] += ' | '+eg["name"]
                r["scraperData"] = eg["id"]
                data += [r]
            i += 1

        return self.standardize(data)

    def standardize(self, data):
        if isinstance(data, list):
            if len(data) > 1:
                dat = []
                for i in data:
                    dat.append(self.subStandardize(i))
                return dat
            elif len(data) == 1:
                return self.subStandardize(data[0])
            else:
                return data
        else:
            return self.subStandardize(data)

    def subStandardize(self, i):
        baseImgUrl = "https://image.tmdb.org/t/p/w500"
        genres = {"28":"Action", "12":"Adventure", "16":"Animation", "35":"Comedy", "80":"Crime", "99":"Documentary", "18":"Drama", "10751":"Family", "14":"Fantasy", "36":"History", "27":"Horror", "10402":"Music", "9648":"Mystery", "10749":"Romance", "878":"Science Fiction", "10770":"TV Movie", "53":"Thriller", "10752":"War", "37":"Western"}
        tmp = {"scraperName": "tmdb", "scraperData": None}

        for j in i.keys():
            if i[j] != None:
                if j == "vote_average":
                    tmp["rating"] = i[j]
                elif j == "first_air_date":
                    tmp["premiered"] = i[j]
                elif j == "backdrop_path":
                    tmp["fanart"] = baseImgUrl + i[j]
                elif j == "poster_path":
                    tmp["icon"] = baseImgUrl + i[j]
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
                    tmp["icon"] = baseImgUrl + i[j]
                elif j == "scraperData":
                    tmp["scraperData"] = i[j]
                    
        return tmp