from abc import ABC, abstractmethod
from app.dbHelper import getSqlConnection
from fuzzywuzzy import fuzz, process


class BaseTracker(ABC):
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
        self._idTracker = idTracker
        self._idUser = idUser
        self._user = user
        self._password = password
        self._address = address
        self._port = port
        self._data = data
        self._connection = getSqlConnection(False)
        self._existingZwIDs = []
        self._existingTrackerData = []
        self._titles = []
        self._titlesData = {}

    def _loadExistingEntries(self, mediaType):
        self._existingZwIDs = []
        self._existingTrackerData = []
        for i in self._getTrackerEntries(mediaType):
            self._existingZwIDs.append(str(i["mediaData"]))
            self._existingTrackerData.append(str(i["trackerData"]))
        self._titles = []
        self._titlesData = {}

    def _updateStatus(
        self, mediaType: int, mediaData: str, count: int, time: int, date: str
    ) -> None:
        cursor = self._connection.cursor(dictionary=True, buffered=True)
        cursor.execute(
            "UPDATE status SET watchCount = %(count)s, watchTime = %(time)s, lastDate = %(date)s WHERE mediaType = %(mediaType)s AND idMedia = %(mediaData)s AND idUser = %(idUser)s",
            {
                "count": count,
                "time": time,
                "date": date,
                "mediaType": mediaType,
                "mediaData": mediaData,
                "idUser": self._idUser,
            },
        )
        self._connection.commit()

    def _addTrackerEntry(
        self, mediaType: int, mediaData: str, trackerData: str, enabled: int = 1
    ) -> None:
        cursor = self._connection.cursor(dictionary=True, buffered=True)
        cursor.execute(
            "INSERT INTO trackers_link (mediaType, mediaData, idTracker, trackerData, enabled) VALUES (%(mediaType)s, %(mediaData)s, %(idTracker)s, %(trackerData)s, %(enabled)s)",
            {
                "mediaType": mediaType,
                "mediaData": mediaData,
                "idTracker": self._idTracker,
                "trackerData": trackerData,
                "enabled": enabled,
            },
        )
        self._existingZwIDs.append(str(mediaData))
        self._existingTrackerData.append(str(trackerData))
        self._connection.commit()

    def _getTrackerEntries(self, mediaType: int, enabled=None) -> list:
        cursor = self._connection.cursor(dictionary=True, buffered=True)
        if enabled is None:
            cursor.execute(
                "SELECT mediaData, trackerData FROM trackers_link WHERE mediaType = %(mediaType)s AND idTracker = %(id)s",
                {"id": self._idTracker, "mediaType": mediaType},
            )
        else:
            cursor.execute(
                "SELECT mediaData, trackerData FROM trackers_link WHERE mediaType = %(mediaType)s AND idTracker = %(id)s AND enabled=%(enabled)s",
                {
                    "id": self._idTracker,
                    "mediaType": mediaType,
                    "enabled": bool(enabled),
                },
            )
        return cursor.fetchall()

    def _searchMatchingZogwineData(self, mediaType, trackerData, t, year=None) -> bool:
        def addTitle(title):
            zwID = self._titlesData[title]["id"]
            if str(zwID) in self._existingZwIDs:
                return False
            self._addTrackerEntry(mediaType, zwID, trackerData)
            self._titles.remove(title)
            del self._titlesData[title]

        if str(trackerData) in self._existingTrackerData:
            return False

        if year is None:
            title, percent = process.extractOne(
                t, self._titles, scorer=fuzz.token_sort_ratio
            )
            if percent > 85:
                addTitle(title)
                return True
            else:
                return False
        else:
            results = []
            for i in process.extract(
                t, self._titles, limit=3, scorer=fuzz.token_sort_ratio
            ):
                if i[1] > 70:
                    if i[0] in self._titlesData and self._titlesData[i[0]]["premiered"][
                        0:4
                    ] == str(year):
                        results.append((i[0], i[1] + 5))
                    else:
                        results.append((i[0], i[1]))
            if len(results) == 0:
                return False
            else:
                maxResID = 0
                for i, r in enumerate(results):
                    if results[maxResID][1] < r[1]:
                        maxResID = i
                addTitle(results[maxResID][0])
                return True

    def _compareStatus(
        self,
        zwWatchCount,
        zwWatchTime,
        zwWatchDate,
        trWatchCount,
        trWatchTime,
        trWatchDate,
        direction=2,
    ) -> int:
        zwWatchTime = int(zwWatchTime)
        trWatchTime = int(trWatchTime)
        # direction: 0 = tracker -> zogwine; 1 = zogwine -> tracker; 2 = zogwine <-> tracker
        # true = update traker with zogwine data
        # false = update zogwine with tracker data
        if direction == 2:
            if (zwWatchDate is not None and zwWatchDate[0:4] != "0000") and (
                trWatchDate is not None
                and len(trWatchDate) >= 4
                and trWatchDate[0:4] != "0000"
                and int(trWatchDate[0:4]) > 1970
            ):
                # if the 2 dates can be compared
                return int(zwWatchDate > trWatchDate)
            elif zwWatchCount != trWatchCount:
                return int(zwWatchCount > trWatchCount)
            elif zwWatchTime != trWatchTime:
                return int(zwWatchTime > trWatchTime)
            else:
                return -1
        elif direction == 1 and (
            zwWatchDate != trWatchDate
            or zwWatchCount != trWatchCount
            or zwWatchTime != trWatchTime
        ):
            return 1
        elif direction == 0 and (
            zwWatchDate != trWatchDate
            or zwWatchCount != trWatchCount
            or zwWatchTime != trWatchTime
        ):
            return 0
        else:
            return -1

    def __del__(self):
        self._connection.close()