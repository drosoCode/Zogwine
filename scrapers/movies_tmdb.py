# coding: utf-8
import requests
import json
import urllib.parse

class tmdb:

    def __init__(self, apikey):
        self._endpoint = "https://api.themoviedb.org/3/"
        self._apikey = apikey
        self._cache = (None, None, None)

    def getMovie(self, id):
        return self.standardize(json.loads(requests.get(self._endpoint+"movie/"+str(id)+"?api_key="+self._apikey).text))

    def searchMovie(self, name, year=-1):
        if year == -1:
            year = ''
        else:
            year = '&year='+str(year)
        next = 1
        data = []
        while next:
            response = json.loads(requests.get(self._endpoint+"search/movie?query="+urllib.parse.quote(name)+year+"&api_key="+self._apikey+"&page="+str(next)).text)
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
                elif j == "title":
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
                elif j == "air_date":
                    tmp["premiered"] = i[j]
                elif j == "release_date":
                    tmp["premiered"] = i[j]
                elif j == "still_path":
                    tmp["icon"] = baseImgUrl + i[j]
                elif j == "scraperData":
                    tmp["scraperData"] = i[j]
                    
        return tmp