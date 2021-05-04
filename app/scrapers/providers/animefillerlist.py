from app.scrapers.interfaces.filler import FillerScraper

from bs4 import BeautifulSoup
import requests
import re


def getFillers(self, url):
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
                        flist.append((v, ftype))
                else:
                    flist.append((int(val), ftype))

    rawData = requests.get(url).text
    soup = BeautifulSoup(rawData, features="html.parser")
    resp = soup.find("div", {"id": "Condensed"})
    if resp is None:
        return []

    fillers = []
    getFillersFromResp(resp, 1, "mixed_canon/filler", fillers)
    getFillersFromResp(resp, 2, "filler", fillers)

    return sorted(fillers, key=lambda filler: filler[0])


def __getFillerSlug(self, name):
    s = name.lower()
    s = re.sub("[._?@!$~#&%*,;:/<>().']+", " ", s)
    s = re.sub(" +(on)|(at)+ +", "", s)
    s = s.replace(" ", "-")
    s = s.strip("-")
    return s


def searchFillers(self, name):
    url = "https://www.animefillerlist.com/shows/" + self.__getFillerSlug(name)
    if requests.get(url).status_code == 200:
        return url
    else:
        return False