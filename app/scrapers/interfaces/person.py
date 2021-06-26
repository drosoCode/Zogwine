from abc import ABC, abstractmethod
from app.scrapers.BaseScraper import BaseScraper
from dataclasses import dataclass


class PersonScraper(BaseScraper, ABC):
    @abstractmethod
    def getPersonDetails(self, id):
        raise NotImplementedError()

    @abstractmethod
    def getPersonData(self, name):
        raise NotImplementedError()


@dataclass(frozen=True)
class PersonData:
    birthdate: str
    deathdate: str
    gender: int
    description: str
    icon: str
    knownFor: str
