from app.scrapers.interfaces.tvs import TVSScraper
import requests
import json
import urllib.parse
from datetime import datetime


class tvdb(TVSScraper):
    def __init__(self, apikey):
        super().__init__(apikey)
        self._endpoint = "https://api.thetvdb.com"
        token = json.loads(
            requests.post(
                self._endpoint + "/login",
                data=json.dumps({"apikey": apikey}),
                headers={
                    "Content-type": "application/json",
                    "Accept": "application/json",
                },
            ).text
        )["token"]
        self._headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Accept-Language": "en",
            "Authorization": "Bearer " + token,
        }

    def __getImg(self, img, isBanner):
        if img is None:
            return None
        else:
            if isBanner:
                return "https://artworks.thetvdb.com/banners/" + img
            else:
                return "https://artworks.thetvdb.com" + img

    def searchTVS(self, name):
        results = []
        resp = json.loads(
            requests.get(
                self._endpoint + "/search/series?name=" + urllib.parse.quote(name),
                headers=self._headers,
            ).text
        )
        if "Error" not in resp and "data" in resp:
            for item in resp["data"]:
                inProd = False
                if item.get("status") == "Continuing":
                    inProd = True
                results.append(
                    {
                        "title": item.get("seriesName"),
                        "overview": item.get("overview"),
                        "in_production": inProd,
                        "icon": self.__getImg(item.get("poster"), False),
                        "premiered": item.get("firstAired"),
                        "id": item.get("id"),
                        "scraperName": "tvdb",
                        "scraperData": None,
                    }
                )
        return results

    def getTVS(self, id):
        resp = json.loads(
            requests.get(
                self._endpoint + "/series/" + str(id), headers=self._headers
            ).text
        )
        if "data" in resp:
            resp = resp["data"]
            return {
                "title": resp.get("seriesName"),
                "overview": resp.get("overview"),
                "icon": self.__getImg(resp.get("poster"), True),
                "fanart": self.__getImg(resp.get("fanart"), True),
                "premiered": resp.get("firstAired"),
                "rating": resp.get("siteRating"),
                "scraperName": "tvdb",
                "scraperData": None,
            }
        else:
            return {
                "title": "TVS " + str(id),
                "overview": "",
                "icon": None,
                "fanart": None,
                "premiered": None,
                "rating": None,
                "scraperName": "tvdb",
                "scraperData": None,
            }

    def getTVSSeason(self, id, season):
        d = json.loads(
            requests.get(
                self._endpoint
                + "/series/"
                + str(id)
                + "/images/query?keyType=season&subKey="
                + str(season),
                headers=self._headers,
            ).text
        )
        try:
            date = json.loads(
                requests.get(
                    self._endpoint
                    + "/series/"
                    + str(id)
                    + "/episodes/query?airedSeason="
                    + str(season)
                    + "&airedEpisode=1",
                    headers=self._headers,
                ).text
            )["data"][0]["firstAired"]
        except Exception:
            date = "Unknown"
        try:
            ic = "https://artworks.thetvdb.com/banners/" + d["data"][0]["fileName"]
        except Exception:
            ic = None
        return {
            "scraperName": "tvdb",
            "scraperData": None,
            "premiered": date,
            "title": "Season " + str(season),
            "overview": "No Data Available",
            "icon": ic,
        }

    def getTVSPeople(self, id):
        d = json.loads(
            requests.get(
                self._endpoint + "/series/" + str(id) + "/actors", headers=self._headers
            ).text
        )
        people = []
        for p in d["data"]:
            people.append([p.get("name"), p.get("role")])
        return people

    def getTVSUpcomingEpisodes(self, id):
        d = json.loads(
            requests.get(
                self._endpoint + "/series/" + str(id) + "/episodes",
                headers=self._headers,
            ).text
        )
        if d["links"]["last"] != 1:
            d = json.loads(
                requests.get(
                    self._endpoint
                    + "/series/"
                    + str(id)
                    + "/episodes?page="
                    + str(d["links"]["last"]),
                    headers=self._headers,
                ).text
            )
        for ep in d["data"]:
            if (
                ep.get("firstAired") is not None
                and ep.get("firstAired") != ""
                and datetime.strptime(ep.get("firstAired"), "%Y-%m-%d") > datetime.now()
            ):
                return {
                    "scraperName": "tvdb",
                    "scraperData": None,
                    "date": ep.get("firstAired"),
                    "title": ep.get("episodeName"),
                    "overview": ep.get("overview"),
                    "season": ep.get("airedSeason"),
                    "episode": ep.get("airedEpisodeNumber"),
                    "icon": None,
                }
        return None

    def getTVSTags(self, idTvs):
        d = json.loads(
            requests.get(
                self._endpoint + "/series/" + str(idTvs), headers=self._headers
            ).text
        )["data"]
        tags = []
        if "network" in d:
            tags.append(["network", d["network"], None])

        if "genre" in d:
            for c in d["genre"]:
                tags.append(["genre", c, None])

        return tags

    def getTVSEpisodes(self, id, season, episode=None, scraperData=None):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "/series/"
                + str(id)
                + "/episodes/query?airedSeason="
                + str(season)
                + "&airedEpisode="
                + str(episode),
                headers=self._headers,
            ).text
        )
        if "data" in resp and len(resp["data"]) > 0:
            resp = resp["data"][0]
            return {
                "title": resp.get("episodeName"),
                "overview": resp.get("overview"),
                "icon": self.__getImg(resp.get("filename"), True),
                "season": resp.get("airedSeason"),
                "episode": resp.get("airedEpisodeNumber"),
                "rating": resp.get("siteRating"),
                "id": resp.get("id"),
                "premiered": resp.get("firstAired"),
                "scraperName": "tvdb",
                "scraperData": None,
            }
        else:
            return {
                "title": "Episode " + str(episode),
                "overview": None,
                "icon": None,
                "season": str(season),
                "episode": str(episode),
                "rating": None,
                "id": None,
                "premiered": None,
                "scraperName": "tvdb",
                "scraperData": None,
            }
