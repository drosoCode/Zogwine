from app.scrapers.BaseScaper import BaseScaper
from app.scrapers.interfaces.movie import MovieScraper
from app.scrapers.interfaces.tvs import TVSScraper
from app.scrapers.interfaces.person import PersonScraper

import requests
import json
import urllib.parse
from datetime import datetime


class tmdb(TVSScraper, MovieScraper, PersonScraper):
    def __init__(self, apikey):
        super().__init__(apikey)
        self._endpoint = "https://api.themoviedb.org/3/"
        self._baseImgUrl = "https://image.tmdb.org/t/p/w500"
        self._apikey = apikey
        self._cache = (None, None, None)

    def __getImg(self, img):
        if img is None:
            return None
        else:
            return self._baseImgUrl + img

    # region TVS

    def getTVS(self, idTvs):
        resp = json.loads(
            requests.get(
                self._endpoint + "tv/" + str(idTvs) + "?api_key=" + self._apikey
            ).text
        )
        return {
            "title": resp.get("name"),
            "overview": resp.get("overview"),
            "icon": self.__getImg(resp.get("poster_path")),
            "fanart": self.__getImg(resp.get("backdrop_path")),
            "premiered": resp.get("first_air_date"),
            "rating": resp.get("vote_average"),
            "scraperName": "tmdb",
            "scraperData": None,
        }

    def getTVSSeason(self, idTvs, season):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "tv/"
                + str(idTvs)
                + "/season/"
                + str(season)
                + "?api_key="
                + self._apikey
            ).text
        )
        n = resp.get("name")
        if n is None:
            n = "Season" + str(season)

        return {
            "scraperName": "tmdb",
            "scraperData": None,
            "premiered": resp.get("air_date"),
            "title": n,
            "overview": resp.get("overview"),
            "icon": self.__getImg(resp.get("poster_path")),
        }

    def getTVSPeople(self, idTvs):
        resp = json.loads(
            requests.get(
                self._endpoint + "tv/" + str(idTvs) + "/credits?api_key=" + self._apikey
            ).text
        )
        people = []
        for p in resp["cast"]:
            people.append([p.get("name"), p.get("character")])
        for p in resp["crew"]:
            people.append([p.get("name"), p.get("department")])
        return people

    def getTVSUpcomingEpisodes(self, idTvs):
        d = json.loads(
            requests.get(
                self._endpoint + "tv/" + str(idTvs) + "?api_key=" + self._apikey
            ).text
        )
        if (
            "next_episode_to_air" in d
            and d["next_episode_to_air"] is not None
            and datetime.strptime(d["next_episode_to_air"]["air_date"], "%Y-%m-%d")
            > datetime.now()
        ):
            return {
                "scraperName": "tmdb",
                "scraperData": None,
                "date": d["next_episode_to_air"].get("air_date"),
                "title": d["next_episode_to_air"].get("name"),
                "overview": d["next_episode_to_air"].get("overview"),
                "season": d["next_episode_to_air"].get("season_number"),
                "episode": d["next_episode_to_air"].get("episode_number"),
                "icon": self.__getImg(d["next_episode_to_air"].get("still_path")),
            }
        return None

    def getTVSTags(self, idTvs):
        d = json.loads(
            requests.get(
                self._endpoint + "tv/" + str(idTvs) + "?api_key=" + self._apikey
            ).text
        )
        tags = []
        if "origin_country" in d:
            tags.append(["country", d["origin_country"][0], None])

        if "network" in d:
            for c in d["networks"]:
                tags.append(
                    ["network", c.get("name"), self.__getImg(c.get("logo_path"))]
                )

        if "production_companies" in d:
            for c in d["production_companies"]:
                tags.append(
                    ["production", c.get("name"), self.__getImg(c.get("logo_path"))]
                )

        if "genres" in d:
            for c in d["genres"]:
                tags.append(["genre", c.get("name"), None])

        return tags

    def getTVSEpisodes(self, id, season, episode, scraperData=None):
        if scraperData == None:
            resp = json.loads(
                requests.get(
                    self._endpoint
                    + "tv/"
                    + str(id)
                    + "/season/"
                    + str(season)
                    + "/episode/"
                    + str(episode)
                    + "?api_key="
                    + self._apikey
                ).text
            )
            return {
                "title": resp.get("name"),
                "overview": resp.get("overview"),
                "icon": self.__getImg(resp.get("still_path")),
                "season": resp.get("season_number"),
                "episode": resp.get("episode_number"),
                "rating": resp.get("vote_average"),
                "id": resp.get("id"),
                "premiered": resp.get("air_date"),
                "scraperName": "tmdb",
                "scraperData": None,
            }
        else:
            if self._cache[0] != id or self._cache[1] != scraperData:
                self._cache = (
                    id,
                    scraperData,
                    json.loads(
                        requests.get(
                            self._endpoint
                            + "tv/episode_group/"
                            + str(scraperData)
                            + "?api_key="
                            + self._apikey
                        ).text
                    ),
                )
            resp = self._cache[2]["groups"]
            if (
                len(resp) > 0
                and 0 <= season - 1 < len(resp)
                and 0 <= episode - 1 < len(resp[season - 1]["episodes"])
            ):
                d = resp[season - 1]["episodes"][episode - 1]
                return {
                    "title": d.get("name"),
                    "overview": d.get("overview"),
                    "icon": self.__getImg(d.get("still_path")),
                    "season": str(season),
                    "episode": str(episode),
                    "rating": d.get("vote_average"),
                    "id": d.get("id"),
                    "premiered": d.get("air_date"),
                    "scraperName": "tmdb",
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
                    "scraperName": "tmdb",
                    "scraperData": None,
                }

    def searchTVS(self, name):
        next = 1
        data = []
        results = []
        while next:
            response = json.loads(
                requests.get(
                    self._endpoint
                    + "search/tv?query="
                    + urllib.parse.quote(name)
                    + "&api_key="
                    + self._apikey
                    + "&page="
                    + str(next)
                ).text
            )
            if response["page"] < response["total_pages"]:
                next += 1
            else:
                next = None
            data += response["results"]
        # check if there is episode groups availables
        i = 0
        d = len(data)
        while i < d:
            res = data[i]
            epGroup = json.loads(
                requests.get(
                    self._endpoint
                    + "tv/"
                    + str(res["id"])
                    + "/episode_groups?api_key="
                    + self._apikey
                ).text
            )["results"]
            for eg in epGroup:
                r = res.copy()
                r["name"] += " | " + eg["name"]
                r["scraperData"] = eg["id"]
                data += [r]
            i += 1

        for item in data:
            results.append(
                {
                    "title": item.get("name"),
                    "overview": item.get("overview"),
                    "in_production": item.get("in_production"),
                    "icon": self.__getImg(item.get("poster_path")),
                    "premiered": item.get("first_air_date"),
                    "id": item.get("id"),
                    "scraperName": "tmdb",
                    "scraperData": item.get("scraperData"),
                }
            )
        return results

    # endregion

    # region Movie

    def getMovie(self, id):
        resp = json.loads(
            requests.get(
                self._endpoint + "movie/" + str(id) + "?api_key=" + self._apikey
            ).text
        )
        c = None
        if (
            "belongs_to_collection" in resp
            and resp["belongs_to_collection"] is not None
            and "id" in resp["belongs_to_collection"]
        ):
            c = resp["belongs_to_collection"]["id"]
        return {
            "title": resp.get("title"),
            "overview": resp.get("overview"),
            "icon": self.__getImg(resp.get("poster_path")),
            "fanart": self.__getImg(resp.get("backdrop_path")),
            "rating": resp.get("vote_average"),
            "id": resp.get("id"),
            "premiered": resp.get("release_date"),
            "scraperName": "tmdb",
            "scraperData": None,
            "collection": c,
        }

    def getMovieCollection(self, id):
        resp = json.loads(
            requests.get(
                self._endpoint + "collection/" + str(id) + "?api_key=" + self._apikey
            ).text
        )
        return {
            "title": resp.get("name"),
            "overview": resp.get("overview"),
            "icon": self.__getImg(resp.get("poster_path")),
            "fanart": self.__getImg(resp.get("backdrop_path")),
            "id": resp.get("id"),
            "premiered": resp["parts"][0].get("release_date"),
            "scraperName": "tmdb",
            "scraperData": None,
        }

    def searchMovie(self, name, year=-1):
        if year == -1:
            year = ""
        else:
            year = "&year=" + str(year)
        next = 1
        data = []
        while next:
            response = json.loads(
                requests.get(
                    self._endpoint
                    + "search/movie?query="
                    + urllib.parse.quote(name)
                    + year
                    + "&api_key="
                    + self._apikey
                    + "&page="
                    + str(next)
                ).text
            )
            if response["page"] < response["total_pages"]:
                next += 1
            else:
                next = None
            data += response["results"]

        results = []
        for item in data:
            results.append(
                {
                    "title": item.get("title"),
                    "overview": item.get("overview"),
                    "icon": self.__getImg(item.get("poster_path")),
                    "premiered": item.get("release_date"),
                    "id": item.get("id"),
                    "scraperName": "tmdb",
                    "scraperData": None,
                }
            )
        return results

    def getMoviePeople(self, idMov):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "movie/"
                + str(idMov)
                + "/credits?api_key="
                + self._apikey
            ).text
        )
        people = []
        for p in resp["cast"]:
            people.append([p.get("name"), p.get("character")])
        for p in resp["crew"]:
            people.append([p.get("name"), p.get("department")])
        return people

    def getMovieTags(self, idMov):
        d = json.loads(
            requests.get(
                self._endpoint + "movie/" + str(idMov) + "?api_key=" + self._apikey
            ).text
        )
        tags = []
        if (
            "production_countries" in d
            and len(d["production_countries"]) > 0
            and "iso_3166_1" in d["production_countries"][0]
        ):
            tags.append(["country", d["production_countries"][0]["iso_3166_1"], None])

        if "production_companies" in d:
            for c in d["production_companies"]:
                tags.append(
                    ["production", c.get("name"), self.__getImg(c.get("logo_path"))]
                )

        if "genres" in d:
            for c in d["genres"]:
                tags.append(["genre", c.get("name"), None])

        return tags

    # endregion

    # region Person
    def getPersonDetails(self, id):
        data = json.loads(
            requests.get(
                self._endpoint + "person/" + str(id) + "?api_key=" + self._apikey
            ).text
        )
        ic = None
        if data.get("profile_path") is not None:
            ic = self.baseImgUrl + data.get("profile_path")
        return {
            "birthdate": data.get("birthday"),
            "deathdate": data.get("deathday"),
            "gender": data.get("gender"),
            "description": data.get("biography"),
            "icon": ic,
            "known_for": data.get("known_for_department"),
        }

    def getPersonData(self, name):
        response = json.loads(
            requests.get(
                self._endpoint
                + "search/person?query="
                + urllib.parse.quote(name)
                + "&api_key="
                + self._apikey
            ).text
        )
        if len(response["results"]) == 0:
            return None
        else:
            return self.getPersonDetails(response["results"][0]["id"])

    # endregion
