from abc import ABC, abstractmethod


class PersonScraper(ABC):
    @abstractmethod
    def getPersonDetails(self, id):
        raise NotImplementedError()

    @abstractmethod
    def getPersonData(self, name):
        raise NotImplementedError()