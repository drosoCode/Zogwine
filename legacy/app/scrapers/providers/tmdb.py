from app.scrapers.interfaces.movie import *
from app.scrapers.interfaces.tvs import *
from app.scrapers.interfaces.person import *
from app.scrapers.interfaces.common import *
from app.scrapers.BaseProvider import BaseProvider
from app.exceptions import NoDataException

import requests
import json
import urllib.parse
from datetime import datetime


class tmdb(BaseProvider, TVSProvider, MovieProvider, PersonProvider):
    """
    def __init__(self, apikey):
        super().__init__()
        self._endpoint = "https://api.themoviedb.org/3/"
        self._baseImgUrl = "https://image.tmdb.org/t/p/w500"
        self._apikey = apikey
        self._cache = (None, None, None)
        self.scraperName = "tmdb"

    def __getImg(self, img):
        if img is None:
            return None
        else:
            return self._baseImgUrl + img
    
    # region TVS

    def getTVS(self):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "tv/"
                + str(self._scraperID)
                + "?api_key="
                + self._apikey
            ).text
        )
        if resp.get("success") == False:
            raise NoDataException()

        return TVSData(
            title=resp.get("name"),
            overview=resp.get("overview"),
            icon=self.__getImg(resp.get("poster_path")),
            fanart=self.__getImg(resp.get("backdrop_path")),
            premiered=resp.get("first_air_date"),
            rating=resp.get("vote_average"),
            scraperName=self.scraperName,
            scraperData=None,
            scraperLink="https://www.themoviedb.org/tv/" + str(self._scraperID),
            scraperID=resp.get("id"),
        )
    
    def getTVSSeason(self, season):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "tv/"
                + str(self._scraperID)
                + "/season/"
                + str(season)
                + "?api_key="
                + self._apikey
            ).text
        )
        if resp.get("success") == False:
            raise NoDataException()

        n = resp.get("name")
        if n is None:
            n = "Season" + str(season)

        return TVSSeasonData(
            scraperName=self.scraperName,
            scraperData=None,
            scraperID=resp.get("id"),
            scraperLink=None,
            premiered=resp.get("air_date"),
            title=n,
            overview=resp.get("overview"),
            icon=self.__getImg(resp.get("poster_path")),
            rating=-1,
        )
    """

    def getTVSPeople(self):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "tv/"
                + str(self._scraperID)
                + "/credits?api_key="
                + self._apikey
            ).text
        )
        people = []
        if "cast" in resp:
            for p in resp["cast"]:
                people.append(
                    PersonData(
                        name=p.get("name"), role=p.get("character"), character=True
                    )
                )

        if "crew" in resp:
            for p in resp["crew"]:
                people.append(
                    PersonData(
                        name=p.get("name"), role=p.get("department"), character=False
                    )
                )
        return people

    def getTVSUpcomingEpisodes(self):
        d = json.loads(
            requests.get(
                self._endpoint
                + "tv/"
                + str(self._scraperID)
                + "?api_key="
                + self._apikey
            ).text
        )
        if d.get("success") == False:
            raise NoDataException()

        if (
            "next_episode_to_air" in d
            and d["next_episode_to_air"] is not None
            and datetime.strptime(d["next_episode_to_air"]["air_date"], "%Y-%m-%d")
            > datetime.now()
        ):
            return TVSUpcomingEpisode(
                scraperName=self.scraperName,
                scraperData=None,
                scraperID=d["next_episode_to_air"].get("id"),
                premiered=d["next_episode_to_air"].get("air_date"),
                title=d["next_episode_to_air"].get("name"),
                overview=d["next_episode_to_air"].get("overview"),
                season=d["next_episode_to_air"].get("season_number"),
                episode=d["next_episode_to_air"].get("episode_number"),
                icon=self.__getImg(d["next_episode_to_air"].get("still_path")),
            )
        return None

    def getTVSTags(self):
        d = json.loads(
            requests.get(
                self._endpoint
                + "tv/"
                + str(self._scraperID)
                + "?api_key="
                + self._apikey
            ).text
        )

        tags = []
        if "origin_country" in d and len(d["origin_country"]) > 0:
            tags.append(
                TagData(name="country", value=d["origin_country"][0], icon=None)
            )

        if "network" in d:
            for c in d["networks"]:
                tags.append(
                    TagData(
                        name="network",
                        value=c.get("name"),
                        icon=self.__getImg(c.get("logo_path")),
                    )
                )

        if "production_companies" in d:
            for c in d["production_companies"]:
                tags.append(
                    TagData(
                        name="production",
                        value=c.get("name"),
                        icon=self.__getImg(c.get("logo_path")),
                    )
                )

        if "genres" in d:
            for c in d["genres"]:
                tags.append(TagData(name="genre", value=c.get("name"), icon=None))

        return tags

    def getTVSEpisode(self, season, episode):
        if self._scraperData == None:
            resp = json.loads(
                requests.get(
                    self._endpoint
                    + "tv/"
                    + str(self._scraperID)
                    + "/season/"
                    + str(season)
                    + "/episode/"
                    + str(episode)
                    + "?api_key="
                    + self._apikey
                ).text
            )
            if resp.get("success") == False:
                raise NoDataException()

            return TVSEpisodeData(
                title=resp.get("name"),
                overview=resp.get("overview"),
                icon=self.__getImg(resp.get("still_path")),
                season=resp.get("season_number") or str(season),
                episode=resp.get("episode_number") or str(episode),
                rating=resp.get("vote_average"),
                scraperID=resp.get("id"),
                premiered=resp.get("air_date"),
                scraperName=self.scraperName,
                scraperData=None,
                scraperLink=None,
            )
        else:
            if self._cache[0] != self._scraperID or self._cache[1] != self._scraperData:
                self._cache = (
                    self._scraperID,
                    self._scraperData,
                    json.loads(
                        requests.get(
                            self._endpoint
                            + "tv/episode_group/"
                            + str(self._scraperData)
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
                return TVSEpisodeData(
                    title=d.get("name"),
                    overview=d.get("overview"),
                    icon=self.__getImg(d.get("still_path")),
                    season=str(season),
                    episode=str(episode),
                    rating=d.get("vote_average"),
                    scraperID=d.get("id"),
                    premiered=d.get("air_date"),
                    scraperName=self.scraperName,
                    scraperData=None,
                    scraperLink=None,
                )
            else:
                return TVSEpisodeData(
                    title="Episode " + str(episode),
                    overview=None,
                    icon=None,
                    season=str(season),
                    episode=str(episode),
                    rating=None,
                    scraperID=None,
                    premiered=None,
                    scraperName=self.scraperName,
                    scraperData=None,
                    scraperLink=None,
                )

    """
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
                MediaSearchData(
                    title=item.get("name"),
                    overview=item.get("overview"),
                    icon=self.__getImg(item.get("poster_path")),
                    premiered=item.get("first_air_date"),
                    scraperID=item.get("id"),
                    scraperName=self.scraperName,
                    scraperData=item.get("scraperData"),
                    scraperLink="https://www.themoviedb.org/tv/" + str(item["id"]),
                )
            )
        return results
    """

    # endregion

    # region Movie

    def getMovie(self):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "movie/"
                + str(self._scraperID)
                + "?api_key="
                + self._apikey
            ).text
        )
        if resp.get("success") == False:
            raise NoDataException()

        c = None
        if (
            "belongs_to_collection" in resp
            and resp["belongs_to_collection"] is not None
            and "id" in resp["belongs_to_collection"]
        ):
            c = resp["belongs_to_collection"]["id"]
        return MovieData(
            title=resp.get("title"),
            overview=resp.get("overview"),
            icon=self.__getImg(resp.get("poster_path")),
            fanart=self.__getImg(resp.get("backdrop_path")),
            rating=resp.get("vote_average"),
            scraperID=resp.get("id"),
            premiered=resp.get("release_date"),
            scraperName=self.scraperName,
            scraperData=None,
            collection=c,
            scraperLink="https://www.themoviedb.org/movie/" + str(self._scraperID),
        )

    def getMovieCollection(self):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "collection/"
                + str(self._scraperID)
                + "?api_key="
                + self._apikey
            ).text
        )
        if resp.get("success") == False:
            raise NoDataException()

        return MovieCollectionData(
            title=resp.get("name"),
            overview=resp.get("overview"),
            icon=self.__getImg(resp.get("poster_path")),
            fanart=self.__getImg(resp.get("backdrop_path")),
            scraperID=resp.get("id"),
            premiered=resp["parts"][0].get("release_date"),
            scraperName=self.scraperName,
            scraperData=None,
            scraperLink=None,
        )

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
                MediaSearchData(
                    title=item.get("title"),
                    overview=item.get("overview"),
                    icon=self.__getImg(item.get("poster_path")),
                    premiered=item.get("release_date"),
                    scraperID=item.get("id"),
                    scraperName=self.scraperName,
                    scraperData=None,
                    scraperLink="https://www.themoviedb.org/movie/" + str(item["id"]),
                )
            )
        return results

    def getMoviePeople(self):
        resp = json.loads(
            requests.get(
                self._endpoint
                + "movie/"
                + str(self._scraperID)
                + "/credits?api_key="
                + self._apikey
            ).text
        )
        people = []
        if "cast" in resp:
            for p in resp["cast"]:
                people.append(
                    PersonData(
                        name=p.get("name"), role=p.get("character"), character=True
                    )
                )

        if "crew" in resp:
            for p in resp["crew"]:
                people.append(
                    PersonData(
                        name=p.get("name"), role=p.get("department"), character=False
                    )
                )
        return people

    def getMovieTags(self):
        d = json.loads(
            requests.get(
                self._endpoint
                + "movie/"
                + str(self._scraperID)
                + "?api_key="
                + self._apikey
            ).text
        )
        tags = []
        if (
            "production_countries" in d
            and len(d["production_countries"]) > 0
            and "iso_3166_1" in d["production_countries"][0]
        ):
            tags.append(
                TagData(
                    name="country",
                    value=d["production_countries"][0]["iso_3166_1"],
                    icon=None,
                )
            )

        if "production_companies" in d:
            for c in d["production_companies"]:
                tags.append(
                    TagData(
                        name="production",
                        value=c.get("name"),
                        icon=self.__getImg(c.get("logo_path")),
                    )
                )

        if "genres" in d:
            for c in d["genres"]:
                tags.append(
                    TagData(
                        name="genre",
                        value=c.get("name"),
                        icon=None,
                    )
                )

        return tags

    # endregion

    # region Person
    def getPersonDetails(self):
        data = json.loads(
            requests.get(
                self._endpoint + "person/" + str(self._scraperID) + "?api_key=" + self._apikey
            ).text
        )
        ic = None
        return PersonDetails(
            birthdate=data.get("birthday"),
            deathdate=data.get("deathday"),
            gender=data.get("gender"),
            description=data.get("biography"),
            icon=self.__getImg(data.get("profile_path")),
            knownFor=data.get("known_for_department"),
            scraperID=data.get("id"),
            scraperName=self.scraperName,
            scraperData=None,
            scraperLink="https://www.themoviedb.org/person/" + str(data["id"])
        )

    def searchPerson(self, name):
        response = json.loads(
            requests.get(
                self._endpoint
                + "search/person?query="
                + urllib.parse.quote(name)
                + "&api_key="
                + self._apikey
            ).text
        )

        results = []
        for item in response["results"]:
            results.append(
                MediaSearchData(
                    title=item.get("name"),
                    overview=None,
                    icon=self.__getImg(item.get("profile_path")),
                    premiered=None,
                    scraperID=item.get("id"),
                    scraperName=self.scraperName,
                    scraperData=None,
                    scraperLink="https://www.themoviedb.org/person/" + str(item["id"]),
                )
            )

        return results
    # endregion
