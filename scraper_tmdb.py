import requests
import json
import urllib.parse

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
            if len(data) > 1:
                dat = []
                for i in data:
                    dat.append(self.subStandardize(i))
                return dat
            else:
                return self.subStandardize(data[0])
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