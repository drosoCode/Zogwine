from dataclasses import dataclass


@dataclass(frozen=True)
class MediaSearchData:
    title: str
    overview: str
    icon: str
    premiered: str
    scraperID: str
    scraperName: str
    scraperData: str
    scraperLink: str


@dataclass(frozen=True)
class PersonData:
    name: str
    role: str
    character: bool


@dataclass(frozen=True)
class TagData:
    name: str
    value: str
    icon: str