from abc import ABC, abstractmethod
from app.scrapers.BaseScaper import BaseScaper


class FillerScraper(ABC):
    @abstractmethod
    def searchFillers(self, name):
        raise NotImplementedError()

    @abstractmethod
    def getFillers(self, data):
        raise NotImplementedError()
