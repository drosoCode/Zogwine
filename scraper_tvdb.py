import requests
import json
import urllib.parse

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
        tmp = {"scraperName":"tvdb"}
        baseImgUrl = "https://artworks.thetvdb.com"
        baseImgUrl2 = "https://artworks.thetvdb.com/banners/"

        for j in i.keys():
            if j == "vote_average":
                tmp["rating"] = i[j]
            elif j == "firstAired":
                tmp["premiered"] = i[j]
            elif j == "banner":
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

