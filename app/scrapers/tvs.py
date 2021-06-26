from app.scrapers.interfaces.tvs import *
from app.scrapers.BaseScraper import BaseScraper
from app.dbHelper import getSqlConnection
from app.log import logger
from app.utils import encodeImg

import os
import time
import pathlib


class tvs(BaseScraper):
    def __init__(self, config):
        super().__init__(TVSScraper, config)
        self.__basePath = ""
        self.__idLib = -1
        self.__autoAdd = False

        self._mediaType = 2

    def scan(self, idLib: int, autoAdd: bool = False, full: bool = False):
        """
        run a scan for tv shows
        Args:
            idLib: id of the library
            autoAdd: if an item must be automatically selected from multiple results
            full: if true, all the items that haven't been update since a month will be updated
        """
        self.__idLib = idLib
        self.__autoAdd = autoAdd
        try:
            self.__basePath = self._getBasePath(self.__idLib)
            tvsData = self.__getTVSData(self.__idLib)
            paths = [x["a"] for x in tvsData]

            for i in os.listdir(self.__basePath):
                try:
                    pos = paths.index(i)
                    if pos < 0:
                        # this is a newly discovered tvs
                        data = self._addTVS(i)
                    else:
                        data = tvsData[pos]
                        if tvsData[pos]["forceUpdate"] > 0:
                            # update tvs metadata [tv_shows, tags, people]
                            self._updateTVS(tvsData[pos])

                    if data is not None:
                        # update tvs files [video_files, seasons, episodes]
                        self._updateEpisodes(data)
                except Exception as e:
                    logger.error(e)

        except Exception as e:
            logger.error(e)

    def _listEpisodes(self, basePath):
        """
        list all absolute paths to episodes in a specified directory
        Args:
            basePath: absolute path to the directory to scan
        """
        episodes = []
        for i in os.listdir(basePath):
            p = os.path.join(basePath, i)
            if os.isdir(p):
                episodes += self._listEpisodes(p)
            else:
                episodes.append(p)
        return episodes

    def _addTVS(self, tvsDir):
        """
        add a newly discovered TV Show
        Args:
            tvsDir: name of the tvs directory
        """
        searchResults = []
        for p in self._getProviders():
            for i in p.searchTVS(tvsDir):
                searchResults.append(i)

        # insert a new tvs and get its id
        idShow = self._insertNewTVS(tvsDir)

        askForSelection = False
        if self.__autoAdd:
            # if the item should be added automatically
            selected = self._selectBestItem(searchResults, tvsDir)
            if selected:
                # if an item was selected with enough confidence
                self.__updateWithSelectionResult(
                    idShow,
                    selected.scraperName,
                    selected.scraperID,
                    selected.scraperData,
                )
            else:
                # else, follow the normal way
                askForSelection = True

        if askForSelection:
            # store the multiple results in the scrapers table to let the user select the right item
            self._addMultipleResults(idShow, searchResults)

    def _updateTVS(self, tvsData):
        provider = self._getProviderFromName(tvsData["scraperName"])
        provider.configure(tvsData["scraperID"], tvsData["scraperData"])
        # update tvs data
        self._updateTVSData(tvsData["idShow"], provider.getTVS())
        # update tvs tags
        for i in provider.getTVSTags():
            pass
        # update tvs people

    # region db utils
    def __getTVSData(self, idLib):
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "SELECT idShow, path, scraperName, scraperID, scraperData, forceUpdate, selectedResult FROM tv_shows WHERE idLib = %(idLib)s;",
            {"idLib": idLib},
        )
        data = cursor.fetchall()
        sqlConnection.close()
        return data

    def __updateWithSelectionResult(
        self, mediaData, scraperName, scraperID, scraperData
    ):
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "UPDATE tv_shows SET scraperID = %(scraperID)s, scraperName = %(scraperName)s, scraperData = %(scraperData)s, forceUpdate = 1 WHERE idShow = %(mediaData)s;",
            {
                "mediaData": mediaData,
                "scraperID": scraperID,
                "scraperName": scraperName,
                "scraperData": scraperData,
            },
        )
        sqlConnection.commit()
        sqlConnection.close()

    def _insertNewTVS(self, tvsDir):
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "INSERT INTO tv_shows (title, selectedResult, path, addDate) VALUES (%(path)s, 0, %(path)s, %(addDate)s);",
            {
                "path": tvsDir,
                "addDate": time.time(),
            },
        )
        sqlConnection.commit()
        cursor.execute(
            "SELECT idShow FROM tv_shows WHERE title = %(path)s AND selectedResult = 0 AND path = %(path)s;",
            {"path": tvsDir},
        )
        idShow = cursor.fetchone()["idShow"]
        sqlConnection.close()
        return idShow

    def _updateTVSData(self, id: int, data: TVSData):
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "UPDATE tv_shows SET title = %(title)s, overview = %(overview)s, icon = %(icon)s, fanart = %(fanart)s, premiered = %(premiered)s, rating = %(rating)s, scraperLink = %(scraperLink)s, scraperData = %(scraperData)s, updateDate = %(updateDate)s, forceUpdate = 0, selectedResult = 1 WHERE idShow = %(mediaData)s;",
            {
                "mediaData": id,
                "title": data.title,
                "overview": data.overview,
                "icon": encodeImg(data.icon),
                "fanart": encodeImg(data.fanart),
                "premiered": data.premiered,
                "rating": data.rating,
                "scraperLink": data.scraperLink,
                "scraperData": data.scraperData,
                "updateDate": time.time(),
            },
        )
        sqlConnection.commit()
        sqlConnection.close()

    # endregion