import os
from importlib import import_module

from .log import logger


class BaseScraper:
    def __init__(self, scraperType):
        self.__scrapers = self.__importScrapers(scraperType)

    def __importScrapers(self, scraperType):
        scrapers = []
        for i in os.listdir("providers"):
            l = len(i)
            if i[l - 3 :] == ".py":
                i = i[0 : l - 3]
                module = import_module("app.scrapers.providers." + i)
                s = getattr(module, i)
                if isinstance(s, scraperType):
                    scrapers.append(s)
        return scrapers

    def __loadCompatibleProviders(className, **kwargs):
        pass

    def scan():
        # load providers for this type
        # start scan
        pass
