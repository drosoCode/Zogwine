from abc import ABC, abstractmethod
from dataclasses import dataclass


class MovieProvider(ABC):
    @abstractmethod
    def getMovieCollection(self):
        raise NotImplementedError()

    @abstractmethod
    def searchMovie(self, name, year=-1):
        raise NotImplementedError()

    @abstractmethod
    def getMoviePeople(self):
        raise NotImplementedError()

    @abstractmethod
    def getMovieTags(self):
        raise NotImplementedError()

    @abstractmethod
    def getMovie(self):
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
