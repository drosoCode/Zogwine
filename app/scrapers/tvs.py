from dataclasses import asdict
from app.scrapers.interfaces.tvs import *
from app.scrapers.interfaces.common import *
from app.scrapers.BaseScraper import BaseScraper
from app.dbHelper import getSqlConnection
from app.log import logger
from app.utils import encodeImg
from app.files import getLibPath, addFile, updateFile
from app.exceptions import InvalidFileException, NoDataException

import os
import time
import pathlib
import re


class tvs(BaseScraper):
    def __init__(self, config):
        super().__init__(TVSScraper, config)
        self.__basePath = ""
        self.__idLib = -1
        self.__autoAdd = False

        self._mediaType = 2

    def scan(self, idLib: int, autoAdd: bool = False):
        """
        run a scan for tv shows
        Args:
            idLib: id of the library
            autoAdd: if an item must be automatically selected from multiple results
        """
        self.__idLib = idLib
        self.__autoAdd = autoAdd
        try:
            self.__basePath = getLibPath(self.__idLib)
            tvsData = self.__getTVSData(self.__idLib)
            paths = [x["a"] for x in tvsData]

            for i in os.listdir(self.__basePath):
                try:
                    currentShow = paths.index(i)
                    if currentShow < 0:
                        # this is a newly discovered tvs
                        data = self._addTVS(i)
                    else:
                        data = tvsData[currentShow]
                        if tvsData[currentShow]["forceUpdate"] > 0:
                            # update tvs metadata [tv_shows, tags, people]
                            self._updateTVS(tvsData[currentShow])

                    if data is not None:
                        # update tvs files [video_files, seasons, episodes]
                        self._updateEpisodes(data)
                except Exception as e:
                    logger.error(e)

        except Exception as e:
            logger.error(e)

    def _listEpisodes(self, basePath, addPath=""):
        """
        list all absolute paths to episodes in a specified directory
        Args:
            basePath: absolute path to the tvs directory
            addPath: optionnal additionnal path after the tvs dir
        """
        episodes = []
        searchDir = os.path.join(basePath, addPath)
        for i in os.listdir(searchDir):
            if os.path.isdir(os.path.join(searchDir, i)):
                episodes += self._listEpisodes(basePath, os.path.join(addPath, i))
            else:
                episodes.append(os.path.join(addPath, i))
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

        askForSelection = not self.__autoAdd
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
        """
        update the data (tvs, tags and people) of a specific tvs
        Args:
            tvsData: data of the tvs to update (retrieved using __getTVSData)
        """
        provider = self._getProviderFromName(tvsData["scraperName"])
        provider.configure(tvsData["scraperID"], tvsData["scraperData"])
        # update tvs data
        self._updateTVSData(tvsData["idShow"], provider.getTVS())
        # update tvs tags
        for i in provider.getTVSTags():
            self._addTag(tvsData["idShow"], i)
        # update tvs people
        for i in provider.getTVSPeople():
            self._addPerson(tvsData["idShow"], i)

    def _updateEpisodes(self, tvsData):
        """
        update the data (episode, season and video_files) of the episodes of a specific tvs
        Args:
            tvsData: data of the tvs (retrieved using __getTVSData)
        """
        sqlConnection, cursor = getSqlConnection()

        # get the path to the tvs dir
        tvsPath = os.path.join(self.__basePath, tvsData["path"])

        # list all existing seasons
        cursor.execute(
            "SELECT season FROM seasons WHERE idShow = %(idShow)s",
            {"idShow": tvsData["idShow"]},
        )
        seasons = []
        for i in cursor.fetchall():
            seasons.append(int(i["season"]))
        # update seasons
        self._updateSeasons(tvsData, seasons)

        # get the correct provider
        provider = self._getProviderFromName(tvsData["scraperName"])
        provider.configure(tvsData["scraperID"], tvsData["scraperData"])

        # list all episode files of this tvs
        for i in self._listEpisodes(tvsPath):
            try:
                # get the path to the episode (without the library path)
                path = os.path.join(tvsData["path"], i)

                # ensure that the path actually exists
                os.stat(path)

                # check if there are existing entries for this episode
                cursor.execute(
                    "SELECT idEpisode, idVid, forceUpdate FROM episodes e, video_files v WHERE e.idVid = v.idVid AND path = %(path)s",
                    {"path": path},
                )
                data = cursor.fetchone()
                if data is not None and "idVid" in data:
                    # the episode already exists, we check if we neeed to update it
                    if data["forceUpdate"]:
                        # update the episode file data
                        idVid = data["idVid"]
                        updateFile(idVid)
                        # update the episode data
                        try:
                            result = provider.getTVSEpisode(season, episode)
                            self._updateEpisodeData(tvsData["idShow"], result)
                        except NoDataException:
                            logger.error(f"no data available for episode {path}")
                else:
                    # we need to create an entry for the episode and for the new video_file
                    idVid = addFile(path, self.__idLib)
                    # extract the season and episode number from the file name
                    item = pathlib.Path(path)
                    seasonSearch = re.findall("(?i)(?:s)(\\d+)(?:e)", item.stem)
                    episodeSearch = re.findall("(?i)(?:s\\d+e)(\\d+)(?:\\.)", item.stem)
                    if len(seasonSearch) == 0 or len(episodeSearch) == 0:
                        raise InvalidFileException(
                            "Cannot determine season/episode number from file name"
                        )

                    season = int(seasonSearch[0])
                    episode = int(episodeSearch[0])
                    # if the season is unknown, add it
                    if season not in seasons:
                        self._createSeason(tvsData, season)
                        seasons.append(season)

                    # add the episode in the database
                    try:
                        result = provider.getTVSEpisode(season, episode)
                        self._insertNewEpisode(tvsData["idShow"], idVid, result)
                    except NoDataException:
                        logger.error(f"no data available for episode {path}")
                        # create a new episode anyway, to allow the user to edit manually the fields
                        self._insertNewEpisode(
                            TVSData(
                                title=item.name,
                                overview="",
                                icon=None,
                                fanart=None,
                                premiered="",
                                rating=-1,
                                scraperID=None,
                                scraperName=provider.scraperName,
                                scraperData=None,
                                scraperLink=None,
                            ),
                            idVid,
                            result,
                        )

                    sqlConnection.commit()
            except Exception as e:
                logger.error(
                    f"Error while scanning episode {path} for tv show {tvsData['idShow']}"
                )
                logger.debug(e)

        sqlConnection.close()

    def _createSeason(self, tvsData, season):
        """
        create a new season for a specific tvs
        Args:
            tvsData: data of the tvs (retrieved using __getTVSData)
            season: the season number
        """
        provider = self._getProviderFromName(tvsData["scraperName"])
        provider.configure(tvsData["scraperID"], tvsData["scraperData"])

        try:
            result = provider.getTVSSeason(season)
            self._insertNewSeason(tvsData["idShow"], season, result)
        except NoDataException:
            logger.error(
                f"no data available for season {season} of tvs {tvsData['idShow']}"
            )

    def _updateSeasons(self, tvsData, seasons):
        """
        update the seasons for a specific tvs
        Args:
            tvsData: data of the tvs (retrieved using __getTVSData)
            seasons: a list of the season numbers to update
        """
        sqlConnection, cursor = getSqlConnection()
        provider = self._getProviderFromName(tvsData["scraperName"])
        provider.configure(tvsData["scraperID"], tvsData["scraperData"])

        for s in seasons:
            cursor.execute(
                "SELECT forceUpdate FROM seasons WHERE idShow = %(idShow)s AND season = %(season)s",
                {"idShow": tvsData["idShow"], "season": s},
            )
            if cursor.fetchone()["forceUpdate"]:
                try:
                    result = provider.getTVSSeason(s)
                    self._updateSeasonData(tvsData["idShow"], s, result)
                except NoDataException:
                    logger.error(
                        f"no data available for season {s} of tvs {tvsData['idShow']}"
                    )
        sqlConnection.close()

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

    def _insertNewEpisode(self, idShow: int, idVid: int, data: TVSEpisodeData):
        sqlConnection, cursor = getSqlConnection()
        queryData = asdict(data).update(
            {
                "addDate": time.time(),
                "idShow": idShow,
                "idVid": idVid,
            }
        )
        cursor.execute(
            "INSERT INTO episodes (title, overview, icon, fanart, premiered, rating, scraperID, scraperName, scraperData, scraperLink, idShow, idVid, addDate, forceUpdate) VALUES (%(title)s, %(overview)s, %(icon)s, %(fanart)s, %(premiered)s, %(rating)s, %(scraperID)s, %(scraperName)s, %(scraperData)s, %(scraperLink)s, %(idShow)s, %(idVid)s, %(addDate)s, 0);",
            queryData,
        )
        sqlConnection.commit()
        sqlConnection.close()

    def _insertNewSeason(self, idShow: int, season: int, data: TVSSeasonData):
        sqlConnection, cursor = getSqlConnection()
        queryData = asdict(data).update(
            {
                "addDate": time.time(),
                "idShow": idShow,
                "season": season,
            }
        )
        cursor.execute(
            "INSERT INTO seasons (title, overview, icon, premiered, rating, scraperID, scraperName, scraperData, scraperLink, idShow, season, addDate, forceUpdate) VALUES (%(title)s, %(overview)s, %(icon)s, %(premiered)s, %(rating)s, %(scraperID)s, %(scraperName)s, %(scraperData)s, %(scraperLink)s, %(idShow)s, %(season)s, %(addDate)s, 0);",
            queryData,
        )
        sqlConnection.commit()
        sqlConnection.close()

    def _updateEpisodeData(self, idEpisode, data: TVSEpisodeData):
        sqlConnection, cursor = getSqlConnection()
        queryData = asdict(data).update(
            {
                "idEpisode": idEpisode,
            }
        )
        cursor.execute(
            "UPDATE episodes SET title = %(title)s, overview = %(overview)s, icon = %(icon)s, fanart = %(fanart)s, premiered = %(premiered)s, rating = %(rating)s, scraperID = %(scraperID)s, scraperName = %(scraperName)s, scraperData = %(scraperData)s, scraperLink = %(scraperLink)s, forceUpdate = 0 WHERE idEpisode = %(idEpisode)s;",
            queryData,
        )
        sqlConnection.commit()
        sqlConnection.close()

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

    def _updateSeasonData(self, idShow: int, season: int, data: TVSSeasonData):
        sqlConnection, cursor = getSqlConnection()
        queryData = asdict(data).update(
            {
                "idShow": idShow,
                "season": season,
            }
        )
        cursor.execute(
            "UPDATE seasons SET title = %(title)s, overview = %(overview)s, icon = %(icon)s, premiered = %(premiered)s, rating = %(rating)s, scraperID = %(scraperID)s, scraperName = %(scraperName)s, scraperData = %(scraperData)s, scraperLink = %(scraperLink)s, forceUpdate = 0 WHERE idShow = %(idShow)s AND season = %(season)s;",
            queryData,
        )
        sqlConnection.commit()
        sqlConnection.close()

    # endregion