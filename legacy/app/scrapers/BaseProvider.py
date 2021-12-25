from abc import ABC, abstractmethod


class BaseProvider(ABC):
    def __init__(self):
        self._scraperID = None
        self._scraperData = None

    def configure(self, scraperID, scraperData=None):
        self._scraperID = scraperID
        self._scraperData = scraperData
