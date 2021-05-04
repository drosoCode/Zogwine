from abc import ABC, abstractmethod
from app.scrapers.BaseScaper import BaseScaper


class MovieScraper(ABC):
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
