from abc import ABC, abstractmethod
from app.scrapers.BaseScraper import BaseScraper


class PersonScraper(BaseScraper, ABC):
    @abstractmethod
    def getPersonDetails(self, id):
        raise NotImplementedError()

    @abstractmethod
    def getPersonData(self, name):
        raise NotImplementedError()


@dataclass
class PersonData:
    birthdate: str
    deathdate: str
    gender: int
    description: str
    icon: str
    knownFor: str


@dataclass
class PersonSearchData:
    name: str
    id: str
