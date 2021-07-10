from .log import logger
from .dbHelper import getSqlConnection
from app.scrapers.BaseScraper import BaseScraper


def __getScraperFromMediaType(mediaType) -> BaseScraper:
    if mediaType == 1 or mediaType == 2:
        from app.scrapers.tvs import tvs

        return tvs({"tmdb": {"apikey": ""}})


def selectScraperResults(mediaType, mediaData, id):
    """
    select a specific result for one item
    Args:
        mediaType: the corresponding item type in database
        mediaData: the corresponding item id in database
        id: the id of the selected result
    """
    __getScraperFromMediaType(mediaType).selectScraperResult(mediaData, id)


def runScan(mediaType, idLib, autoAdd=False):
    __getScraperFromMediaType(mediaType).scan(idLib, autoAdd)
