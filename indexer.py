import re
import os
import json
import requests
import sys
import urllib.parse
from importlib import import_module

from log import logger

class scanner:

    def __init__(self, dbConnection, sType, apiKeys):
        self._class = None
        sys.path.append('scrapers/')
        #load class for specified type
        for i in os.listdir('scrapers/'):
            if i == sType+'_main.py':
                module = import_module(sType+'_main')
                my_class = getattr(module, i[0:i.rfind('_')])
                self._class = my_class(logger, dbConnection, apiKeys)
                break
        if self._class == None:
            logger.error('Failed to import indexer for type '+str(sType))
        else:
            logger.info('Indexer Class Instancied Successfully for type '+str(sType))

    def scanDir(self, path):
        if self._class == None:
            logger.error('Indexer not available')
            return None
        else:
            return self._class.scanDir(path)

    def getTvsNextEps(self, scraperName, scraperID):
        return self._class.getTvsNextEps(scraperName, scraperID)

    def scanPersons(self):
        return self._class.scan()