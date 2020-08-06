# coding: utf-8
import requests
import json
import urllib.parse

class tmdb:

    def __init__(self, apikey):
        self._endpoint = "https://api.themoviedb.org/3/"
        self._baseImgUrl = "https://image.tmdb.org/t/p/w500"
        self._apikey = apikey
        self._cache = (None, None, None)

    def getImg(self, img):
        if img is None:
            return None
        else:
            return self._baseImgUrl + img

    def getMovie(self, id):
        resp = json.loads(requests.get(self._endpoint+"movie/"+str(id)+"?api_key="+self._apikey).text)
        return {
                'title': resp.get('title'),
                'overview': resp.get('overview'),
                'icon': self.getImg(resp.get('poster_path')),
                'fanart': self.getImg(resp.get('backdrop_path')),
                'rating': resp.get('vote_average'),
                'id': resp.get('id'),
                'premiered': resp.get('release_date'),
                'scraperName': 'tmdb',
                'scraperData': None
            }

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

        results = []
        for item in data:
            results.append({
                'title': item.get('title'),
                'overview': item.get('overview'),
                'icon': self.getImg(item.get('poster_path')),
                'premiered': item.get('release_date'),
                'id': item.get('id'),
                'scraperName': 'tmdb',
                'scraperData': None
            })
        return results

    def getPersons(self, idMov):
        resp = json.loads(requests.get(self._endpoint+"movie/"+str(idMov)+"/credits?api_key="+self._apikey).text)
        persons = []
        for p in resp['cast']:
            persons.append([p.get('name'), p.get('character')])
        for p in resp['crew']:
            persons.append([p.get('name'), p.get('department')])
        return persons

    def getTags(self, idMov):
        d = json.loads(requests.get(self._endpoint+"movie/"+str(idMov)+"?api_key="+self._apikey).text)
        tags = []
        if 'production_countries' in d and len(d['production_countries']) > 0 and 'iso_3166_1' in d['production_countries'][0]:
            tags.append(['country', d['production_countries'][0]['iso_3166_1'], None])

        if 'production_companies' in d:
            for c in d['production_companies']:
                tags.append(['production', c.get('name'), self.getImg(c.get('logo_path'))])

        if 'genres' in d:
            for c in d['genres']:
                tags.append(['genre', c.get('name'), None])

        return tags
