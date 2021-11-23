from app.scrapers.interfaces.person import *
from app.scrapers.BaseScraper import BaseScraper
from app.dbHelper import getSqlConnection
from app.log import logger
from app.utils import encodeImg
from app.exceptions import NoDataException

import time
from dataclasses import asdict

class person(BaseScraper):
    def __init__(self, config):
        super().__init__(PersonProvider, config)
        self._mediaType = 7
    
    def scan(self, idLib = None, autoAdd = True):
        for p in self._getPersonData():
            if p["scraperID"] is None:
                searchResults = []
                for provider in self._getProviders():
                    for i in provider.searchPerson(p["name"]):
                        searchResults.append(i)
                        
                if len(searchResults) > 0:
                    ## TODO: Implement autoAdd=False
                    selected = self._selectBestItem(searchResults, p["name"])
                    if not selected:
                        selected = searchResults[0]

                    self._updateWithSelectionResult(
                        p["idPers"],
                        selected.scraperName,
                        selected.scraperID,
                        selected.scraperData,
                    )
                    self._updatePerson(self._getPersonData(p["idPers"]))
            else:
                self._updatePerson(p)

    def _updatePerson(self, p):
        provider = self._getProviderFromName(p["scraperName"])
        provider.configure(p["scraperID"], p["scraperData"])

        sqlConnection, cursor = getSqlConnection()
        try:
            queryData = asdict(provider.getPersonDetails())
            queryData.update(
                {
                    "updateDate": round(time.time()),
                    "icon": encodeImg(queryData["icon"]),
                    "idPers": p["idPers"],
                }
            )
            cursor.execute(
                "UPDATE people SET gender = %(gender)s, birthdate = %(birthdate)s, deathdate = %(deathdate)s, description = %(description)s, known_for = %(knownFor)s, icon = %(icon)s, updateDate = %(updateDate)s, forceUpdate = 0 WHERE idPers = %(idPers)s;",
                queryData,
            )
            sqlConnection.commit()
        except NoDataException:
            logger.error(
                f"no data available for person with id {p['scraperID']}"
            )
        finally:
            sqlConnection.close()

    def _updateWithSelectionResult(
        self, mediaData, scraperName, scraperID, scraperData
    ):
        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "UPDATE people SET scraperID = %(scraperID)s, scraperName = %(scraperName)s, scraperData = %(scraperData)s, forceUpdate = 1 WHERE idPers = %(mediaData)s;",
            {
                "mediaData": mediaData,
                "scraperID": scraperID,
                "scraperName": scraperName,
                "scraperData": scraperData,
            },
        )
        sqlConnection.commit()
        sqlConnection.close()

    def _getPersonData(self, idPers=None):
        sqlConnection, cursor = getSqlConnection()
        if idPers is None:
            cursor.execute("SELECT * FROM people WHERE forceUpdate = 1 OR scraperID IS NULL")
            data = cursor.fetchall()
        else:
            cursor.execute("SELECT * FROM people WHERE idPers  = %(idPers)s", {"idPers": idPers})
            data = cursor.fetchone()
        sqlConnection.close()
        return data