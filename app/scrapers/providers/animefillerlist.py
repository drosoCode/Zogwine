from app.scrapers.interfaces.filler import FillerProvider, FillerType, FillerData
from app.scrapers.BaseProvider import BaseProvider
from app.scrapers.interfaces.common import MediaSearchData

from bs4 import BeautifulSoup
import requests
from fuzzywuzzy import process

class animefillerlist(BaseProvider, FillerProvider):
    SUPPORTED_MEDIA_TYPES = [1]

    def __init__(self):
        super().__init__()
        self._endpoint = "https://www.animefillerlist.com/shows/"
        self._scraperName = "animefillerlist"

    def getFiller(self):
        def getFillersFromResp(resp, ftype, name, flist):
            r = resp.find("div", {"class": name})
            if r is None:
                return None
            for ep in r.find("span", {"class": "Episodes"}):
                if hasattr(ep, "contents"):
                    val = ep.contents[0]
                    if "-" in val:
                        sp = val.split("-")
                        for v in range(int(sp[0]), int(sp[1]) + 1):
                            flist.append(FillerData(
                                absoluteNumber=int(v),
                                filler=ftype
                            ))
                    else:
                        flist.append(FillerData(
                            absoluteNumber=int(val),
                            filler=ftype
                        ))

        rawData = requests.get(self._endpoint + self._scraperID).text
        soup = BeautifulSoup(rawData, features="html.parser")
        resp = soup.find("div", {"id": "Condensed"})
        if resp is None:
            return []

        fillers = []
        getFillersFromResp(resp, FillerType.CANON, "manga_canon", fillers)
        getFillersFromResp(resp, FillerType.ADAPTATION, "anime_canon", fillers)
        getFillersFromResp(resp, FillerType.MIXED, "mixed_canon/filler", fillers)
        getFillersFromResp(resp, FillerType.FILLER, "filler", fillers)

        return sorted(fillers, key=lambda filler: filler.absoluteNumber)

    def searchFiller(self, name):
        rawData = requests.get(self._endpoint).text
        soup = BeautifulSoup(rawData, features="html.parser")
        resp = soup.find_all("a")
        titles = []
        slugs = []
        for a in resp:
            if a.href[0:7] == "/shows/":
                titles.append(a.innerText)
                slugs.append(a.href[7:])

        results = []
        for i in process.extract(name, titles, limit=5):
            if i[1] > 50:
                slug = slugs[titles.index(i[0])]
                results.append(
                    MediaSearchData(
                        title=i[0],
                        overview=None,
                        icon=None,
                        premiered=None,
                        scraperID=slug,
                        scraperName=self._scraperName,
                        scraperData=None,
                        scraperLink=self._endpoint + slug
                    )
                )
