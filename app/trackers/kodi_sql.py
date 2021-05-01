from app.dbHelper import getSqlConnection
from app.log import logger
from app.exceptions import InvalidArgument
from app.trackers.TVSTracker import TVSTracker

from mysql.connector import MySQLConnection


class kodi(TVSTracker):
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
        self.__kodiConn = MySQLConnection(
            host=self._address,
            user=self._user,
            passwd=self._password,
            db=self._data,
            port=self._port,
        )

    def scanTVS(self):
        kodiCursor = self.__kodiConn.cursor(dictionary=True, buffered=True)
        existingZwIDs = []
        existingKodiIDs = []
        for i in self._getTrackerEntries(2):
            existingZwIDs.append(i["mediaData"])
            existingKodiIDs.append(i["trackerData"])

        kodiCursor.execute("SELECT idShow, c00, c05 FROM tvshow")
        for i in kodiCursor.fetchall():
            self._searchMatchingZogwineShow(i["idShow"], i["c00"], year=i["c05"][0:4])

    def syncTVSv1(self, direction: int = 2):
        # direction: 0 = kodi -> zogwine; 1 = zogwine -> kodi; 2 = zogwine <-> kodis
        # SELECT c00, playCount, lastPlayed, resumeTimeInSeconds, totalTimeInSeconds FROM episode_view WHERE idShow = 29 AND c12 = 1 AND c13 = 24
        # SELECT c00, watchedCount FROM tvshow_view WHERE idShow = 29
        kodiCursor = self.__kodiConn.cursor(dictionary=True, buffered=True)

        for i in self._getTrackerEntries(2, True):
            kodiCursor.execute(
                "SELECT idEpisode, c12, c13, playCount, lastPlayed, resumeTimeInSeconds, totalTimeInSeconds FROM episode_view WHERE idShow = %(idShow)s ORDER BY c12, c13",
                {"idShow": i["trackerData"]},
            )
            kodiData = {}
            for k in kodiCursor.fetchall():
                kodiData[(k["c12"], k["c13"])] = k

            zwData = self._getEpisodesFromShow(i["mediaData"])

            kodiDataMax = kodiData.keys()
            kodiDataMax = kodiDataMax[len(kodiDataMax) - 1]

            for ep in zwData:
                x = (ep["season"], ep["episode"])
                if (x in kodiData) and (
                    kodiData[x]["playCount"] != ep["watchCount"]
                    or kodiData[x]["resumeTimeInSeconds"] != ep["watchTime"]
                ):
                    if direction == 2:
                        if (
                            ep["lastDate"] is not None
                            or kodiData[x]["lastPlayed"] is not None
                        ) and ep["watchCount"] >= kodiData[x]["playCount"]:
                            updateKodi(kodiCursor, kodiData[x], ep)
                        elif ep["resumeTimeInSeconds"] >= kodiData[x]["watchTime"]:
                            updateKodi(kodiCursor, kodiData[x], ep)
                        else:
                            self._updateStatus(
                                1,
                                ep["idEpisode"],
                                kodiData[x]["playCount"],
                                kodiData[x]["resumeTimeInSeconds"],
                                kodiData[x]["lastPlayed"],
                            )
                    elif direction == 1:
                        updateKodi(kodiCursor, kodiData[x], ep)
                    elif direction == 0:
                        self._updateStatus(
                            1,
                            ep["idEpisode"],
                            kodiData[x]["playCount"],
                            kodiData[x]["resumeTimeInSeconds"],
                            kodiData[x]["lastPlayed"],
                        )

        self.__kodiConn.commit()

        def updateKodi(cursor, kodiData, zwData):
            cursor.execute(
                "UPDATE episode_view SET playCount = %(count)s, resumeTimeInSeconds = %(duration)s, lastPlayed = %(date)s WHERE idEpisode = %(idEpisode)s",
                {
                    "count": zwData["watchCount"],
                    "time": zwData["watchTime"],
                    "date": zwData["lastDate"],
                    "idEpisode": kodiData["idEpisode"],
                },
            )

    def syncTVS(self, direction: int = 2):
        # direction: 0 = kodi -> zogwine; 1 = zogwine -> kodi; 2 = zogwine <-> kodi
        print("sync")
        kodiCursor = self.__kodiConn.cursor(dictionary=True, buffered=True)

        for i in self._getTrackerEntries(2, True):
            kodiCursor.execute(
                "SELECT idEpisode, c12, c13, playCount, lastPlayed, resumeTimeInSeconds FROM episode_view WHERE idShow = %(idShow)s ORDER BY c12, c13",
                {"idShow": i["trackerData"]},
            )
            kodiData = {}
            for k in kodiCursor.fetchall():
                kodiData[(k["c12"], k["c13"])] = k

            zwData = self._getEpisodesFromShow(i["mediaData"])

            for ep in zwData:
                x = (ep["season"], ep["episode"])
                if (x in kodiData) and (
                    kodiData[x]["playCount"] != ep["watchCount"]
                    or kodiData[x]["resumeTimeInSeconds"] != ep["watchTime"]
                ):
                    if self._compare(
                        ep["watchCount"],
                        ep["watchTime"],
                        ep["lastDate"],
                        kodiData[x]["playCount"],
                        kodiData[x]["resumeTimeInSeconds"],
                        kodiData[x]["lastPlayed"],
                        direction,
                    ):
                        kodiCursor.execute(
                            "UPDATE episode_view SET playCount = %(count)s, resumeTimeInSeconds = %(duration)s, lastPlayed = %(date)s WHERE idEpisode = %(idEpisode)s",
                            {
                                "count": ep["watchCount"],
                                "time": ep["watchTime"],
                                "date": ep["lastDate"],
                                "idEpisode": kodiData["idEpisode"],
                            },
                        )
                        self.__kodiConn.commit()
                    else:
                        self._updateStatus(
                            1,
                            ep["idEpisode"],
                            kodiData[x]["playCount"],
                            kodiData[x]["resumeTimeInSeconds"],
                            kodiData[x]["lastPlayed"],
                        )

    def scanMovie(self):
        pass

    def syncMovie(self, direction: int = 2):
        pass

    def __del__(self):
        super().__del__()
        self.__kodiConn.close()