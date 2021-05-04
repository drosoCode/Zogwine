from abc import ABC, abstractmethod


class TVSScraper(ABC):
    @abstractmethod
    def searchTVS(self, name):
        raise NotImplementedError()

    @abstractmethod
    def getTVSEp(self, id, season, episode, scraperData=None):
        raise NotImplementedError()

    @abstractmethod
    def getTVSTags(self, idTvs):
        raise NotImplementedError()

    @abstractmethod
    def getTVSUpcomingEpisode(self, idTvs):
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