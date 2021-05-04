from abc import ABC, abstractmethod


class MovieScraper(ABC):
    @abstractmethod
    def getMovie(self, id):
        raise NotImplementedError()

    @abstractmethod
    def getCollection(self, id):
        raise NotImplementedError()

    @abstractmethod
    def searchMovie(self, name, year=-1):
        raise NotImplementedError()

    @abstractmethod
    def getPeople(self, idMov):
        raise NotImplementedError()

    @abstractmethod
    def getTags(self, idMov):
        raise NotImplementedError()
