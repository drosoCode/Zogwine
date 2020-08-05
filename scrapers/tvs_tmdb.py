# coding: utf-8
import requests
import json
import urllib.parse
from datetime import datetime

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

    def getTVS(self, idTvs):
        resp = json.loads(requests.get(self._endpoint+"tv/"+str(idTvs)+"?api_key="+self._apikey).text)
        return {
            'title': resp.get('name'),
            'overview': resp.get('overview'),
            'icon': self.getImg(resp.get('poster_path')),
            'fanart': self.getImg(resp.get('backdrop_path')),
            'premiered': resp.get('first_air_date'),
            'rating': resp.get('vote_average'),
            'scraperName': 'tmdb',
            'scraperData': None
        }

    def getTVSSeason(self, idTvs, season):
        resp = json.loads(requests.get(self._endpoint+"tv/"+str(idTvs)+"/season/"+str(season)+"?api_key="+self._apikey).text)
        n = resp.get('name')
        if n is None:
            n = "Season"+str(season)
        
        return {
                   'scraperName': 'tmdb',
                   'scraperData': None,
                   'premiered': resp.get('air_date'),
                   'title': n,
                   'overview': resp.get('overview'),
                   'icon': self.getImg(resp.get('poster_path'))
                }

    def getPersons(self, idTvs):
        resp = json.loads(requests.get(self._endpoint+"tv/"+str(idTvs)+"/credits?api_key="+self._apikey).text)
        persons = []
        for p in resp['cast']:
            persons.append([p.get('name'), p.get('character')])
        for p in resp['crew']:
            persons.append([p.get('name'), p.get('department')])
        return persons

    def getUpcomingEpisode(self, idTvs):
        d = json.loads(requests.get(self._endpoint+"tv/"+str(idTvs)+"?api_key="+self._apikey).text)
        if 'next_episode_to_air' in d and d['next_episode_to_air'] is not None and datetime.strptime(d['next_episode_to_air']['air_date'], '%Y-%m-%d') > datetime.now():
            return {
                    'scraperName': 'tmdb',
                    'scraperData': None,
                    'date': d['next_episode_to_air'].get('air_date'),
                    'title': d['next_episode_to_air'].get('name'),
                    'overview': d['next_episode_to_air'].get('overview'),
                    'season': d['next_episode_to_air'].get('season_number'),
                    'episode': d['next_episode_to_air'].get('episode_number'),
                    'icon': self.getImg(d['next_episode_to_air'].get('still_path'))
                }
        return None

    def getTags(self, idTvs):
        d = json.loads(requests.get(self._endpoint+"tv/"+str(idTvs)+"?api_key="+self._apikey).text)
        tags = []
        if 'origin_country' in d:
            tags.append(['country', d['origin_country'][0], None])

        if 'network' in d:
            for c in d['networks']:
                tags.append(['network', c.get('name'), self.getImg(c.get('logo_path'))])

        if 'production_companies' in d:
            for c in d['production_companies']:
                tags.append(['production', c.get('name'), self.getImg(c.get('logo_path'))])

        if 'genres' in d:
            for c in d['genres']:
                tags.append(['genre', c.get('name'), None])

        return tags

    def getTVSEp(self, id, season, episode, scraperData=None):
        if scraperData == None:
            resp = json.loads(requests.get(self._endpoint+"tv/"+str(id)+"/season/"+str(season)+"/episode/"+str(episode)+"?api_key="+self._apikey).text)
            return {
                'title': resp.get('name'),
                'overview': resp.get('overview'),
                'icon': self.getImg(resp.get('still_path')),
                'season': resp.get('season_number'),
                'episode': resp.get('episode_number'),
                'rating': resp.get('vote_average'),
                'id': resp.get('id'),
                'premiered': resp.get('air_date'),
                'scraperName': 'tmdb',
                'scraperData': None
            }
        else:
            if self._cache[0] != id or self._cache[1] != scraperData:
                self._cache = (id, scraperData, json.loads(requests.get(self._endpoint+"tv/episode_group/"+str(scraperData)+"?api_key="+self._apikey).text))
            resp = self._cache[2]["groups"]
            if len(resp) > 0 and 0 <= season-1 < len(resp) and 0 <= episode-1 < len(resp[season-1]["episodes"]):
                d = resp[season-1]["episodes"][episode-1]
                return self.standardize(d)
                return {
                    'title': d.get('name'),
                    'overview': d.get('overview'),
                    'icon': self.getImg(d.get('still_path')),
                    'season': str(season),
                    'episode': str(episode),
                    'rating': d.get('vote_average'),
                    'id': d.get('id'),
                    'premiered': resp.get('air_date'),
                    'scraperName': 'tmdb',
                    'scraperData': None
                }
            else:
                return {
                    'title': 'Episode '+str(episode),
                    'overview': None,
                    'icon': None,
                    'season': str(season),
                    'episode': str(episode),
                    'rating': None,
                    'id': None,
                    'premiered': None,
                    'scraperName': 'tmdb',
                    'scraperData': None
                }

    def searchTVS(self, name):
        next = 1
        data = []
        results = []
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
        
        for item in data:
            results.append({
                'title': item.get('name'),
                'overview': item.get('overview'),
                'in_production': item.get('in_production'),
                'icon': self.getImg(item.get('poster_path')),
                'premiered': item.get('first_air_date'),
                'id': item.get('id'),
                'scraperName': 'tmdb',
                'scraperData': item.get('scraperData')
            })
        return results