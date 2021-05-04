from app.dbHelper import getSqlConnection
from app.log import logger
from app.exceptions import InvalidArgument
from app.trackers.TVSTracker import TVSTracker
from app.trackers.MovieTracker import MovieTracker

import requests
import json


class kodi(TVSTracker, MovieTracker):
    def __init__(
        self,
        idTracker: int,
        idUser: int,
        user: str,
        password: str = None,
        address: str = None,
        port: int = None,
        data: str = None,
    ):
        super().__init__(idTracker, idUser, user, password, address, port or 3306, data)
        if self._user is not None and self._password is not None:
            self._auth = (str(self._user), str(self._password))
        else:
            self._auth = None

    def __apiCall(self, data):
        return requests.post(
            "http://" + self._address + ":" + str(self._port) + "/jsonrpc",
            auth=self._auth,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

    def scanTVS(self):
        self._loadTVSData()
        existingZwIDs = []
        existingKodiIDs = []
        for i in self._getTrackerEntries(2):
            existingZwIDs.append(i["mediaData"])
            existingKodiIDs.append(i["trackerData"])

        data = self.__apiCall(
            {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "id": 1,
                "params": {"properties": ["year"]},
            }
        ).json()["result"]["tvshows"]
        for i in data:
            self._searchMatchingZogwineShow(i["tvshowid"], i["label"], year=i["year"])

    def syncTVS(self, direction: int = 2):
        self._loadTVSData()
        # direction: 0 = kodi -> zogwine; 1 = zogwine -> kodi; 2 = zogwine <-> kodi
        for i in self._getTrackerEntries(2, True):
            data = self.__apiCall(
                {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.GetEpisodes",
                    "id": 1,
                    "params": {
                        "tvshowid": int(i["trackerData"]),
                        "properties": [
                            "playcount",
                            "lastplayed",
                            "resume",
                            "season",
                            "episode",
                        ],
                    },
                }
            ).json()["result"]["episodes"]
            kodiData = {}
            for k in data:
                kodiData[(k["season"], k["episode"])] = k

            for ep in self._getEpisodesFromShow(i["mediaData"]):
                x = (ep["season"], ep["episode"])
                if (x in kodiData) and (
                    kodiData[x]["playcount"] != ep["watchCount"]
                    or kodiData[x]["resume"]["position"] != ep["watchTime"]
                ):
                    action = self._compareStatus(
                        ep["watchCount"],
                        ep["watchTime"],
                        ep["lastDate"],
                        kodiData[x]["playcount"],
                        kodiData[x]["resume"]["position"],
                        kodiData[x]["lastplayed"],
                        direction,
                    )
                    if action == 1:
                        self.__apiCall(
                            {
                                "jsonrpc": "2.0",
                                "method": "VideoLibrary.SetEpisodeDetails",
                                "id": 1,
                                "params": {
                                    "episodeid": kodiData[x]["episodeid"],
                                    "playcount": ep["watchCount"],
                                    "lastplayed": ep["lastDate"],
                                    "resume": {"position": ep["watchTime"]},
                                    # "resume": {"position": ep["watchTime"], "total": 0},
                                },
                            }
                        )
                    elif action == 0:
                        self._updateStatus(
                            1,
                            ep["idEpisode"],
                            kodiData[x]["playcount"],
                            kodiData[x]["resume"]["position"],
                            kodiData[x]["lastplayed"],
                        )

    def scanMovie(self):
        self._loadMovieData()

        existingZwIDs = []
        existingKodiIDs = []
        for i in self._getTrackerEntries(3):
            existingZwIDs.append(i["mediaData"])
            existingKodiIDs.append(i["trackerData"])

        data = self.__apiCall(
            {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies",
                "id": 1,
                "params": {"properties": ["year"]},
            }
        ).json()["result"]["movies"]
        for i in data:
            self._searchMatchingZogwineMovie(i["movieid"], i["label"], year=i["year"])

    def syncMovie(self, direction: int = 2):
        self._loadMovieData()
        data = self.__apiCall(
            {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies",
                "id": 1,
                "params": {
                    "properties": ["playcount", "lastplayed", "resume"],
                },
            }
        ).json()["result"]["movies"]
        kodiData = {}
        for k in data:
            kodiData[k["movieid"]] = k
        kodiDataKeys = list(kodiData.keys())

        for i in self._getTrackerEntries(3, True):
            if int(i["trackerData"]) in kodiDataKeys:
                zwMov = self._getMovieStatus(i["mediaData"])
                kodiMov = kodiData[int(i["trackerData"])]

                action = self._compareStatus(
                    zwMov["watchCount"],
                    zwMov["watchTime"],
                    zwMov["lastDate"],
                    kodiMov["playcount"],
                    kodiMov["resume"]["position"],
                    kodiMov["lastplayed"],
                    direction,
                )

                if action == 1:
                    self.__apiCall(
                        {
                            "jsonrpc": "2.0",
                            "method": "VideoLibrary.SetMovieDetails",
                            "id": 1,
                            "params": {
                                "movieid": kodiMov["movieid"],
                                "playcount": zwMov["watchCount"],
                                "lastplayed": zwMov["lastDate"],
                                "resume": {"position": zwMov["watchTime"]},
                            },
                        }
                    )
                elif action == 0:
                    self._updateStatus(
                        3,
                        i["mediaData"],
                        kodiMov["playcount"],
                        kodiMov["resume"]["position"],
                        kodiMov["lastplayed"],
                    )
