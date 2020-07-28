# coding: utf-8
import re
import os
import json
import urllib.parse
from importlib import import_module
from base64 import b64encode

class persons:

    def __init__(self, logger, dbConnection, apiKeys):
        self._logger = logger
        self._apiKeys = apiKeys
        self._connection = dbConnection
        self._scrapers = []
        self.importScrapers()
        self._currentMovie = None
        logger.info('Persons Indexer Initialised Successfully')

    def encodeImg(self, img):
        if img is not None and img != "":
            return b64encode(img.encode()).decode()
        else:
            return None

    def importScrapers(self):
        for i in os.listdir('scrapers/'):
            if 'persons_' in i and i[i.rfind('.')+1:] == 'py' and 'main' not in i:
                try:
                    scraperName = i[i.rfind('_')+1:i.rfind('.')]
                    module = import_module('persons_'+scraperName)
                    my_class = getattr(module, scraperName)
                    if my_class.__name__ in self._apiKeys:
                        instance = my_class(self._apiKeys[my_class.__name__])
                        self._scrapers.append(instance)
                        self._logger.info('Scraper '+str(my_class.__name__)+' successfully initialised')
                    else:
                        self._logger.warning('Failed to import scraper '+str(my_class.__name__))
                except:
                    self._logger.warning('Failed to import scraper '+str(my_class.__name__))

    def scan(self):
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM persons WHERE forceUpdate = 1 OR gender IS NULL")

        for p in cursor.fetchall():
            self._logger.info('Person: '+str(p['name']))
            data = {
                'gender': [p['gender']],
                'birthdate': [p['birthdate']],
                'deathdate': [p['deathdate']],
                'description': [p['description']],
                'known_for': [p['known_for']],
                'icon': [p['icon']]
            }
            for s in self._scrapers:
                d = s.getPersonData(p['name'])
                if d is not None:
                    data['gender'].append(d.get('gender'))
                    data['birthdate'].append(d.get('birthdate'))
                    data['deathdate'].append(d.get('deathdate'))
                    data['description'].append(d.get('description'))
                    data['known_for'].append(d.get('known_for'))
                    data['icon'].append(d.get('icon'))
                
            queryData = {
                'gender': self.pickBest(data['gender']),
                'birthdate': self.pickBest(data['birthdate']),
                'deathdate': self.pickBest(data['deathdate']),
                'description': self.pickBestStr(data['description']),
                'known_for': self.pickBestStr(data['known_for']),
                'icon': self.pickImage(data['icon']),
                'idPers': p['idPers']
            }
            cursor.execute("UPDATE persons SET gender = %(gender)s, birthdate = %(birthdate)s, deathdate = %(deathdate)s, description = %(description)s, known_for = %(known_for)s, icon = %(icon)s, forceUpdate = 0 WHERE idPers = %(idPers)s;", queryData)
            
        self._connection.commit()
        self._logger.debug(str(cursor.rowcount)+'were affected')

    def pickBest(self, data):
        for d in data:
            if d is not None and d != '':
                return d
        return None

    def pickBestStr(self, data):
        keep = []
        for d in data:
            if d is not None and d != '':
                keep.append(d)
        if len(keep) == 0:
            return None
        maxLen = 0
        maxLenIndex = 0
        for i in range(len(keep)):
            if len(keep[i]) > maxLen:
                maxLen = len(keep[i])
                maxLenIndex = i
        return keep[maxLenIndex]

    def pickImage(self, data):
        d = self.pickBest(data)
        if d is None or d[0:5] == 'aHR0c':
            return d
        else:
            return self.encodeImg(d)
        

