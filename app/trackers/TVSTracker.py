from abc import ABC, abstractmethod
from app.trackers.BaseTracker import BaseTracker
from fuzzywuzzy import fuzz, process


class TVSTracker(BaseTracker, ABC):
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
        super().__init__(idTracker, idUser, user, password, address, port, data)
        self._loadTVSData()

    def _loadTVSData(self):
        self._loadExistingEntries(2)

        cursor = self._connection.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT idShow AS id, title, premiered FROM tv_shows")
        for i in cursor.fetchall():
            self._titles.append(i["title"])
            self._titlesData[i["title"]] = i

    def _getEpisodesFromShow(self, idShow) -> list:
        cursor = self._connection.cursor(dictionary=True, buffered=True)
        cursor.execute(
            "SELECT idEpisode, season, episode, COALESCE(watchCount, 0) AS watchCount, COALESCE(watchTime, 0) AS watchTime, lastDate "
            "FROM status s RIGHT JOIN episodes e ON (s.idMedia = e.idEpisode AND s.idUser = %(idUser)s AND s.mediaType = 1)"
            "WHERE idShow = %(idShow)s ORDER BY season, episode",
            {"idShow": idShow, "idUser": self._idUser},
        )
        return cursor.fetchall()

    def _searchMatchingZogwineShow(self, trackerData, t, year=None):
        return self._searchMatchingZogwineData(2, trackerData, t, year)

    @abstractmethod
    def scanTVS(self):
        raise NotImplementedError

    @abstractmethod
    def syncTVS(self):
        raise NotImplementedError
