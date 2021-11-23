from abc import ABC, abstractmethod
from dataclasses import dataclass


class PersonProvider(ABC):
    @abstractmethod
    def getPersonDetails(self):
        raise NotImplementedError()

    @abstractmethod
    def searchPerson(self, name):
        raise NotImplementedError()


@dataclass(frozen=True)
class PersonDetails:
    birthdate: str
    deathdate: str
    gender: int
    description: str
    icon: str
    knownFor: str
    scraperID: str
    scraperName: str
    scraperData: str
    scraperLink: str
