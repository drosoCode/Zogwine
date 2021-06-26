from abc import ABC, abstractmethod
from dataclasses import dataclass


class TVSScraper(ABC):
    @abstractmethod
    def searchTVS(self, name):
        raise NotImplementedError()

    @abstractmethod
    def getTVSEpisodes(self, season, episode):
        raise NotImplementedError()

    @abstractmethod
    def getTVSTags(self):
        raise NotImplementedError()

    @abstractmethod
    def getTVSUpcomingEpisodes(self):
        raise NotImplementedError()

    @abstractmethod
    def getTVSPeople(self):
        raise NotImplementedError()

    @abstractmethod
    def getTVSSeason(self, season):
        raise NotImplementedError()

    @abstractmethod
    def getTVS(self):
        raise NotImplementedError()


@dataclass(frozen=True)
class TVSData:
    title: str
    overview: str
    icon: str
    fanart: str
    premiered: str
    rating: float
    scraperID: str
    scraperName: str
    scraperData: str
    scraperLink: str


@dataclass(frozen=True)
class TVSSeasonData:
    title: str
    overview: str
    premiered: str
    icon: str
    scraperID: str
    scraperName: str
    scraperData: str
    scraperLink: str


@dataclass(frozen=True)
class TVSTagData:
    name: str
    value: str
    icon: str


@dataclass(frozen=True)
class TVSPersonData:
    name: str
    role: str


@dataclass(frozen=True)
class TVSEpisodeData:
    title: str
    overview: str
    icon: str
    season: int
    episode: int
    rating: float
    scraperID: str
    premiered: str
    scraperName: str
    scraperData: str
    scraperLink: str


@dataclass(frozen=True)
class TVSUpcomingEpisode:
    title: str
    overview: str
    season: int
    episode: int
    icon: str
    premiered: str
    scraperID: str
    scraperName: str
    scraperData: str
