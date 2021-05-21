from abc import ABC, abstractmethod


class FillerScraper(BaseScraper, ABC):
    @abstractmethod
    def searchFillers(self, name):
        raise NotImplementedError()

    @abstractmethod
    def getFillers(self, data):
        raise NotImplementedError()
