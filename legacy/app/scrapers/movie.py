from app.scrapers.interfaces.common import *
from app.scrapers.interfaces.movie import *
from app.scrapers.BaseScraper import BaseScraper
from app.common import VIDEO_FILES
from app.dbHelper import getSqlConnection
from app.log import logger
from app.utils import encodeImg
from app.files import getLibPath, addFile, updateFile
from app.exceptions import InvalidFileException, NoDataException

import time
import pathlib
import re
from dataclasses import asdict


class movie(BaseScraper):
    def __init__(self, config):
        super().__init__(MovieProvider, config)
        self.__basePath = ""
        self.__idLib = -1
        self.__autoAdd = False
        self.__addUnknown = True
        self._mediaType = 3
    
    def scan(self, idLib: int, autoAdd: bool = False):
        """
        run a scan for movies
        Args:
            idLib: id of the library
            autoAdd: if an item must be automatically selected from multiple results
        """
        self.__idLib = idLib
        self.__autoAdd = autoAdd

        try:
            self.__basePath = getLibPath(self.__idLib)
            movieData = self._getMovieData(self.__idLib)
            paths = [x["path"] for x in movieData]

            for i in self._listFiles(self.__basePath):
                try:
                    try:
                        currentMovie = paths.index(i)
                        if movieData[currentMovie]["forceUpdate"] > 0:
                            # update movie metadata [data, tags, people]
                            if movieData[currentMovie]["scraperID"] is None or movieData[currentMovie]["scraperName"] is None:
                                # if no scraper is associated, re-run a search
                                self._addMovie(movieData[currentMovie]["title"], movieData[currentMovie]["idMovie"])
                            else:
                                self._updateMovie(movieData[currentMovie])
                    except ValueError:
                        # this is a newly discovered movie
                        self._addMovie(i)

                except Exception as e:
                    # TODO: FIX UTF8 ERROR
                    logger.exception(e)

            # update collection data
            for i in self._getCollectionData():
                if i["forceUpdate"] > 0:
                    self._updateCollection(i)

        except Exception as e:
            logger.exception(e)

    def _updateCollection(self, collectionData):
        provider = self._getProviderFromName(collectionData["scraperName"])
        provider.configure(collectionData["scraperID"], collectionData["scraperData"])
        try:
            self._updateCollectionData(
                collectionData["idCollection"], provider.getMovieCollection()
            )
        except NoDataException:
            logger.error(
                f"no data available for collection with id {collectionData['scraperID']}"
            )

    def _updateMovie(self, movieData):
        """
        update the data (data, tags and people) of a specific movie
        Args:
            movieData: data of the movie to update (retrieved using _getMovieData)
        """
        provider = self._getProviderFromName(movieData["scraperName"])
        provider.configure(movieData["scraperID"], movieData["scraperData"])

        # update movie data
        movieProviderData = provider.getMovie()

        # ensure that the collection exists
        idCollection = None
        if movieProviderData.collection is not None:
            collectionData = self._getCollectionData(idMovie=movieData["idMovie"])
            if collectionData is None:
                collectionData = self._getCollectionData(scraperName=movieProviderData.scraperName, scraperID=movieProviderData.collection)
                if collectionData is None:
                    provider.configure(movieProviderData.collection, None)
                    idCollection = self._insertNewCollection(provider.getMovieCollection())
                else:
                    # set idCollection
                    idCollection = collectionData["idCollection"]
            else:
                idCollection = collectionData["idCollection"]

        movieData.update(
            self._updateMovieData(movieData["idMovie"], movieProviderData, idCollection)
        )
        # update file data
        updateFile(movieData["idVid"])
        # update movie tags
        for i in provider.getMovieTags():
            self._addTag(movieData["idMovie"], i)
        # update movie people
        for i in provider.getMoviePeople():
            self._addPerson(movieData["idMovie"], i)

        return movieData

    def _addMovie(self, path, idMovie=None):
        """
        add a newly discovered movie
        Args:
            path: path to the movie file
        """
        if idMovie is None:
            item = pathlib.Path(path)
            if item.suffix[1:].lower() not in VIDEO_FILES:
                raise InvalidFileException(f"File extension {item.suffix} is not supported")
            name, year = self.__getName(item.stem)
        else:
            name = path
            year = None

        searchResults = []
        for p in self._getProviders():
            for i in p.searchMovie(name.encode("utf8", "surrogateescape"), year):
                searchResults.append(i)

        if len(searchResults) > 0 or self.__addUnknown:
            if idMovie is None:
                # insert a new movie and get its id
                idVid = addFile(path, self.__idLib)
                idMovie = self._insertNewMovie(name, idVid)
            else:
                idMovie = int(idMovie)

            if self.__autoAdd:
                # if the item should be added automatically
                selected = self._selectBestItem(searchResults, name, year)
                if selected:
                    # if an item was selected with enough confidence
                    self._updateWithSelectionResult(
                        idMovie,
                        selected.scraperName,
                        selected.scraperID,
                        selected.scraperData,
                    )
                    return self._updateMovie(self._getMovieData(idMovie=idMovie))

            # store the multiple results in the scrapers table to let the user select the right item
            self._addMultipleResults(idMovie, searchResults)
        return None

    def __getName(self, fileName):
        regex = "(?i)^(.+?)[._( \\t]*(?:(19\\d{2}|20(?:0\\d|1[0-9]))|(fansub|VOST|bluray|\\d+p|brrip|webrip|hdrip|hevc|x26|h26)|(\\[.*\\])|(mkv|avi|mpe?g|mp4)$)"
        find = re.findall(regex, fileName)
        year = None
        if len(find) > 0 and len(find[0][0]) > 0:
            name = find[0][0]
            if len(find[0][1]) == 4:
                year = find[0][1]
        else:
            name = fileName
        name = name.replace("_", " ").replace(".", " ")

        return (name, year)

    # region db utils
    def _getMovieData(self, idLib=None, idMovie=None):
        sqlConnection, cursor = getSqlConnection()
        if idMovie is None:
            cursor.execute(
                "SELECT idMovie, path, title, scraperName, scraperID, scraperData, forceUpdate, m.idVid FROM movies m INNER JOIN video_files v ON (m.idVid = v.idVid) WHERE idLib = %(idLib)s;",
                {"idLib": idLib},
            )
            data = cursor.fetchall()
        else:
            cursor.execute(
                "SELECT idMovie, path, title, scraperName, scraperID, scraperData, forceUpdate, m.idVid FROM movies m INNER JOIN video_files v ON (m.idVid = v.idVid) WHERE idMovie = %(idMovie)s;",
                {"idMovie": idMovie},
            )
            data = cursor.fetchone()

        sqlConnection.close()
        return data

    def _updateMovieData(self, id: int, data: MovieData, idCollection):
        sqlConnection, cursor = getSqlConnection()

        cursor.execute(
            "UPDATE movies SET title = %(title)s, overview = %(overview)s, icon = %(icon)s, fanart = %(fanart)s, premiered = %(premiered)s, rating = %(rating)s, scraperLink = %(scraperLink)s, scraperData = %(scraperData)s, updateDate = %(updateDate)s, idCollection = %(idCollection)s, forceUpdate = 0 WHERE idMovie = %(mediaData)s;",
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
                "updateDate": round(time.time()),
                "idCollection": idCollection,
            },
        )
        sqlConnection.commit()
        sqlConnection.close()

        # return equivalent data to _getMovieData method (without path)
        return {
            "idMovie": id,
            "scraperName": data.scraperName,
            "scraperID": data.scraperID,
            "scraperData": data.scraperData,
            "forceUpdate": 0,
        }

    def _getCollectionData(self, idMovie=None, idCollection=None, scraperName=None, scraperID=None):
        sqlConnection, cursor = getSqlConnection()

        if idMovie is not None:
            cursor.execute(
                "SELECT * FROM movie_collections c INNER JOIN movies m ON (c.idCollection = m.idCollection) WHERE idMovie = %(idMovie)s;",
                {"idMovie": idMovie},
            )
            data = cursor.fetchone()
        elif idCollection is not None:
            cursor.execute(
                "SELECT * FROM movie_collections WHERE idCollection = %(idCollection)s;",
                {"idCollection": idCollection},
            )
            data = cursor.fetchone()
        elif scraperName is not None and scraperID is not None:
            cursor.execute(
                "SELECT * FROM movie_collections WHERE scraperID = %(scraperID)s AND scraperName = %(scraperName)s;",
                {"scraperName": scraperName, "scraperID": scraperID},
            )
            data = cursor.fetchone()
        else:
            cursor.execute("SELECT * FROM movie_collections;")
            data = cursor.fetchall()
        sqlConnection.close()
        return data

    def _insertNewCollection(self, data: MovieCollectionData):
        sqlConnection, cursor = getSqlConnection()
        queryData = asdict(data)
        queryData.update(
            {
                "addDate": round(time.time()),
                "icon": encodeImg(queryData["icon"]),
                "fanart": encodeImg(queryData["fanart"]),
            }
        )
        cursor.execute(
            "INSERT INTO movie_collections (title, overview, premiered, icon, fanart, scraperName, scraperID, scraperData, scraperLink, forceUpdate, addDate, updateDate) VALUES (%(title)s, %(overview)s, %(premiered)s, %(icon)s, %(fanart)s, %(scraperName)s, %(scraperID)s, %(scraperData)s, %(scraperLink)s, 0, %(addDate)s, %(addDate)s);",
            queryData,
        )
        sqlConnection.commit()

        cursor.execute(
            "SELECT idCollection FROM movie_collections WHERE title = %(title)s AND addDate = %(addDate)s;",
            {"title": queryData["title"], "addDate": queryData["addDate"]},
        )
        idCollection = cursor.fetchone()["idCollection"]
        sqlConnection.close()

        return idCollection

    def _updateCollectionData(self, id: int, data: MovieCollectionData):
        sqlConnection, cursor = getSqlConnection()
        queryData = asdict(data)
        queryData.update(
            {
                "updateDate": round(time.time()),
                "icon": encodeImg(queryData["icon"]),
                "fanart": encodeImg(queryData["fanart"]),
                "idCollection": id,
            }
        )
        cursor.execute(
            "UPDATE movie_collections title = %(title)s, overview = %(overview)s, premiered = %(premiered)s, icon = %(icon)s, fanart = %(fanart)s, scraperName = %(scraperName)s, scraperID = %(scraperID)s, scraperData = %(scraperData)s, scraperLink = %(scraperLink)s, forceUpdate = 0, updateDate = %(updateDate)s WHERE idCollection = %(idCollection)s);",
            queryData,
        )
        sqlConnection.commit()
        sqlConnection.close()

    def _updateWithSelectionResult(
        self, mediaData, scraperName, scraperID, scraperData
    ):
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "UPDATE movies SET scraperID = %(scraperID)s, scraperName = %(scraperName)s, scraperData = %(scraperData)s, forceUpdate = 1 WHERE idMovie = %(mediaData)s;",
            {
                "mediaData": mediaData,
                "scraperID": scraperID,
                "scraperName": scraperName,
                "scraperData": scraperData,
            },
        )
        sqlConnection.commit()
        sqlConnection.close()

    def _insertNewMovie(self, name, idVid):
        sqlConnection, cursor = getSqlConnection()
        queryData = {"title": name, "idVid": idVid, "addDate": round(time.time())}
        cursor.execute(
            "INSERT INTO movies (title, addDate, updateDate, idVid) VALUES (%(title)s, %(addDate)s, %(addDate)s, %(idVid)s);",
            queryData,
        )
        sqlConnection.commit()
        cursor.execute(
            "SELECT idMovie FROM movies WHERE title = %(title)s AND scraperID IS NULL AND idVid = %(idVid)s AND addDate = %(addDate)s;",
            queryData,
        )
        idMovie = cursor.fetchone()["idMovie"]

        sqlConnection.close()

        return idMovie

    # endregion