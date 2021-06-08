from abc import ABC, abstractmethod


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


@dataclass
class TVSData:
    title: str
    overview: str
    icon: str
    fanart: str
    permiered: str
    rating: float
    scraperName: str
    scraperData: str
    scraperLink: str
    scraperID: str


@dataclass
class TVSSeasonData:
    title: str
    overview: str
    premiered: str
    icon: str
    scraperID: str
    scraperName: str
    scraperData: str


@dataclass
class TVSTagData:
    name: str
    value: str
    icon: str


@dataclass
class TVSPersonData:
    name: str
    role: str


@dataclass
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


@dataclass
class TVSSearchData:
    title: str
    overview: str
    inProduction: str
    icon: str
    premiered: str
    scraperID: str
    scraperName: str
    scraperData: str


@dataclass
class TVSUpcomingEpisode:
    title: str
    overview: str
    season: int
    episode: int
    icon: str
    date: str
    scraperID: str
    scraperName: str
    scraperData: str
