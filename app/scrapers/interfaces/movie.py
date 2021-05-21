from abc import ABC, abstractmethod


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
