from abc import ABC, abstractmethod
from app.scrapers.BaseScraper import BaseScraper
from app.scrapers.interfaces.base import BaseSearchData
from dataclasses import dataclass


class MovieScraper(BaseScraper, ABC):
    @abstractmethod
    def getMovieCollection(self, id):
        raise NotImplementedError()

    @abstractmethod
    def getCollection(self, id):
        raise NotImplementedError()

    @abstractmethod
    def searchMovie(self, name, year=-1):
        raise NotImplementedError()

    @abstractmethod
    def getMoviePeople(self, idMov):
        raise NotImplementedError()

    @abstractmethod
    def getMovieTags(self, idMov):
        raise NotImplementedError()


@dataclass(frozen=True)
class MovieData:
    title: str
    overview: str
    icon: str
    fanart: str
    rating: float
    premiered: str
    collection: int
    scraperID: str
    scraperName: str
    scraperData: str
    scraperLink: str


@dataclass(frozen=True)
class MovieCollectionData:
    title: str
    overview: str
    icon: str
    fanart: str
    premiered: str
    scraperID: str
    scraperName: str
    scraperData: str
    scraperLink: str

