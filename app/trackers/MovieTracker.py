from abc import ABC, abstractmethod
from app.trackers.BaseTracker import BaseTracker
from fuzzywuzzy import fuzz, process


class MovieTracker(BaseTracker, ABC):
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
        self._loadMovieData()

    def _loadMovieData(self):
        self._loadExistingEntries(3)

        cursor = self._connection.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT idMovie AS id, title, premiered FROM movies")
        for i in cursor.fetchall():
            self._titles.append(i["title"])
            self._titlesData[i["title"]] = i

    def _searchMatchingZogwineMovie(self, trackerData, t, year=None):
        return self._searchMatchingZogwineData(3, trackerData, t, year)

    def _getMovieStatus(self, idMovie) -> list:
        cursor = self._connection.cursor(dictionary=True, buffered=True)
        cursor.execute(
            "SELECT watchCount, watchTime, lastDate FROM status WHERE mediaType = 3 AND idMedia = %(idMovie)s AND idUser = %(idUser)s",
            {"idMovie": idMovie, "idUser": self._idUser},
        )
        return cursor.fetchall()

    @abstractmethod
    def scanMovie(self):
        raise NotImplementedError

    @abstractmethod
    def syncMovie(self):
        raise NotImplementedError