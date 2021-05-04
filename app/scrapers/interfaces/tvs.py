from abc import ABC, abstractmethod
from app.scrapers.BaseScaper import BaseScaper


class TVSScraper(ABC):
    @abstractmethod
    def searchTVS(self, name):
        raise NotImplementedError()

    @abstractmethod
    def getTVSEpisodes(self, id, season, episode, scraperData=None):
        raise NotImplementedError()

    @abstractmethod
    def getTVSTags(self, idTvs):
        raise NotImplementedError()

    @abstractmethod
    def getTVSUpcomingEpisodes(self, idTvs):
        raise NotImplementedError()

    @abstractmethod
    def getTVSPeople(self, idTvs):
        raise NotImplementedError()

    @abstractmethod
    def getTVSSeason(self, idTvs, season):
        raise NotImplementedError()

    @abstractmethod
    def getTVS(self, idTvs):
        raise NotImplementedError()
