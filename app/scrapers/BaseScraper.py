import os
from importlib import import_module
from fuzzywuzzy import fuzz, process
import json
from dataclasses import asdict
import time

from app.log import logger
from app.dbHelper import getSqlConnection
from app.exceptions import UnknownScraperException
from app.utils import encodeImg
from app.scrapers.interfaces.common import TagData, PersonData


class BaseScraper:
    def __init__(self, scraperType, config):
        self._scraperType = scraperType
        self.__providersConfig = config
        self._providers = None

    def _getProviders(self):
        if self._providers is None:
            self._providers = self.__importProviders()
        return self._providers

    def __importProviders(self):
        """
        import all the compatible providers for this scraperType
        """
        providers = []
        logger.info("loading provider for scraper type: " + str(self._scraperType))
        for i in os.listdir("app/scrapers/providers"):
            l = len(i)
            if i[l - 3 :] == ".py":
                name = i[0 : l - 3]
                module = import_module("app.scrapers.providers." + name)
                provider = getattr(module, name)
                if (
                    issubclass(provider, self._scraperType)
                    and name in self.__providersConfig
                ):
                    logger.info("imported provider: " + name)
                    providers.append(provider(**self.__providersConfig[name]))
        return providers

    def _getProviderFromName(self, scraperName):
        for i in self._getProviders():
            if i.__class__.__name__ == scraperName:
                return i
        raise UnknownScraperException(
            f"provider {scraperName} cannot be found for scraper {self.__class__.__name__}"
        )

    def _addScraperResults(self, mediaData, data):
        """
        add a row in database when there is mutliple results available for one item
        Args:
            mediaData: the corresponding item id in database
            data: an array of json objects with the multiple results
        """
        logger.debug(
            f"adding mutiple results for mediaType {self._mediaType} and mediaData {mediaData}"
        )
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "INSERT INTO scrapers (mediaType, mediaData, data) VALUES (%(mediaType)s, %(mediaData)s, %(data)s);",
            {"mediaType": self._mediaType, "mediaData": mediaData, "data": data},
        )
        sqlConnection.close()

    def _selectBestItem(self, items, title, year=None):
        searchItems = []
        if year is not None:
            for i in items:
                if i.year == year:
                    searchItems.append(i)
        else:
            searchItems = items

        titles = [i.title for i in searchItems]

        result, percent = process.extractOne(
            title, titles, scorer=fuzz.token_sort_ratio
        )
        if percent > 85:
            return searchItems[titles.index(result)]
        else:
            return False

    def _addMultipleResults(self, mediaData, searchResults):
        serializedResults = json.dumps([asdict(i) for i in searchResults])
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "INSERT INTO selections (mediaType, mediaData, data) VALUES (%(mediaType)s, %(mediaData)s, %(data)s);",
            {
                "mediaType": self._mediaType,
                "mediaData": mediaData,
                "data": serializedResults,
            },
        )
        sqlConnection.commit()
        sqlConnection.close()

    def selectScraperResult(self, mediaData, id):
        logger.debug(
            f"selected result #{id} for mediaType {self._mediaType} and mediaData {mediaData}"
        )
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "SELECT data FROM selections WHERE mediaType = %(mediaType)s AND mediaData = %(mediaData)s;",
            {"mediaType": self._mediaType, "mediaData": mediaData},
        )
        data = cursor.fetchone().get("data")
        if data is not None and id < len(data):
            # delete selection row
            cursor.execute(
                "DELETE FROM selections WHERE mediaType = %(mediaType)s AND mediaData = %(mediaData)s;",
                {"mediaType": self._mediaType, "mediaData": mediaData},
            )
            data = json.loads(data)
            # update entry
            self._updateWithSelectionResult(
                mediaData,
                data[id]["scraperName"],
                data[id]["scraperID"],
                data[id]["scraperData"],
            )
        sqlConnection.commit()
        sqlConnection.close()

    # region common db methods

    def _addTag(self, mediaData: str, tag: TagData):
        sqlConnection, cursor = getSqlConnection()

        reqData = {"name": tag.name, "value": tag.value}
        cursor.execute(
            "SELECT idTag FROM tags where name = %(name)s AND value = %(value)s;",
            reqData,
        )
        idTag = cursor.fetchone()
        if idTag == None:
            # create tag if new
            cursor.execute(
                "INSERT INTO tags (name, value, icon) VALUES (%(name)s, %(value)s, %(icon)s);",
                {"name": tag.name, "value": tag.value, "icon": encodeImg(tag.icon)},
            )
            # get tag id
            cursor.execute(
                "SELECT idTag FROM tags where name = %(name)s AND value = %(value)s;",
                reqData,
            )
            idTag = cursor.fetchone()["idTag"]
        else:
            idTag = idTag["idTag"]

        # link tag to media
        cursor.execute(
            "INSERT INTO tags_link (idTag, idMedia, mediaType) VALUES (%(idTag)s, %(mediaData)s, %(mediaType)s);",
            {"idTag": idTag, "mediaData": mediaData, "mediaType": self._mediaType},
        )

        sqlConnection.commit()
        sqlConnection.close()

    def _addPerson(self, mediaData: str, person: PersonData):
        sqlConnection, cursor = getSqlConnection()

        cursor.execute(
            "SELECT idPers FROM people where name = %(name)s;",
            {"name": person.name},
        )
        idPers = cursor.fetchone()
        if idPers == None:
            reqData = {"name": person.name, "updateDate": round(time.time())}
            # create person if new
            cursor.execute(
                "INSERT INTO people (name, updateDate, forceUpdate) VALUES (%(name)s, %(updateDate)s, 1);",
                reqData,
            )
            # get person id
            cursor.execute(
                "SELECT idPers FROM people where name = %(name)s AND updateDate = %(updateDate)s;",
                reqData,
            )
            idPers = cursor.fetchone()["idPers"]
        else:
            idPers = idPers["idPers"]

        # link tag to media
        cursor.execute(
            "INSERT INTO people_link (idPers, idMedia, mediaType, role) VALUES (%(idPers)s, %(mediaData)s, %(mediaType)s, %(role)s);",
            {
                "idPers": idPers,
                "mediaData": mediaData,
                "mediaType": self._mediaType,
                "role": person.role,
            },
        )

        sqlConnection.commit()
        sqlConnection.close()

    # endregion
