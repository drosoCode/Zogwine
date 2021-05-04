from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @abstractmethod
    def __init__(self, apikey=None):
        self._apikey = apikey
