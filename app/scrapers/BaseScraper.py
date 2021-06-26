import os
from importlib import import_module
from fuzzywuzzy import fuzz, process
import json
from dataclasses import asdict

from app.log import logger
from app.dbHelper import getSqlConnection, configData
from app.exceptions import InvalidLibraryException, UnknownScraperException


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
        for i in os.listdir("providers"):
            l = len(i)
            if i[l - 3 :] == ".py":
                name = i[0 : l - 3]
                module = import_module("app.scrapers.providers." + name)
                provider = getattr(module, name)
                if (
                    isinstance(provider, self._scraperType)
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

    def _getBasePath(self, idLib):
        """
        returns the absolute path to the root folder of a library
        Args:
            idLib: the library id
        """
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "SELECT path FROM libraries WHERE id = %(id)s;",
            {"id": idLib},
        )
        data = cursor.fetchone()
        sqlConnection.close()
        if data is not None and data.get("path") is not None:
            return os.path.join(
                configData["config"]["contentPath"],
                data["path"],
            )
        else:
            raise InvalidLibraryException(f"library not found for id {idLib}")

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
            "INSERT INTO scrapers (mediaType, mediaData, data) VALUES (%(mediaType)s, %(mediaData)s, %(data)s);",
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
            "SELECT data FROM scrapers WHERE mediaType = %(mediaType)s AND mediaData = %(mediaData)s;",
            {"mediaType": self._mediaType, "mediaData": mediaData},
        )
        data = cursor.fetchone().get("data")
        if data is not None and id < len(data):
            # delete scrapers row
            cursor.execute(
                "DELETE FROM scrapers WHERE mediaType = %(mediaType)s AND mediaData = %(mediaData)s;",
                {"mediaType": self._mediaType, "mediaData": mediaData},
            )
            # update entry
            self.__updateWithSelectionResult(
                mediaData,
                data[id]["scraperName"],
                data[id]["scraperID"],
                data[id]["scraperData"],
            )
        sqlConnection.commit()
        sqlConnection.close()
