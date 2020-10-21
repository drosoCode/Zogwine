import requests
import json
import urllib.parse

class tmdb:

    def __init__(self, apikey):
        self._endpoint = "https://api.themoviedb.org/3/"
        self.baseImgUrl = "https://image.tmdb.org/t/p/w500"
        self._apikey = apikey

    def getPersonDetails(self, id):
        data = json.loads(requests.get(self._endpoint+"person/"+str(id)+"?api_key="+self._apikey).text)
        ic = None
        if data.get('profile_path') is not None:
            ic = self.baseImgUrl + data.get('profile_path')
        return {
            'birthdate': data.get('birthday'),
            'deathdate': data.get('deathday'),
            'gender': data.get('gender'),
            'description': data.get('biography'),
            'icon': ic,
            'known_for': data.get('known_for_department')
        }

    def getPersonData(self, name):
        response = json.loads(requests.get(self._endpoint+"search/person?query="+urllib.parse.quote(name)+"&api_key="+self._apikey).text)
        if len(response['results']) == 0:
            return None
        else:
            return self.getPersonDetails(response["results"][0]['id'])