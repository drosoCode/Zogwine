from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum

class FillerProvider(ABC):
    @abstractmethod
    def searchFiller(self, name):
        raise NotImplementedError()

    @abstractmethod
    def getFiller(self):
        raise NotImplementedError()

class FillerType(IntEnum):
    CANON = 0 # canon with the original support (lightnovel, manga, ...)
    ADAPTATION = 1 # canon in the adaptation (ex: anime with a diverging story)
    MIXED = 2 # only a part of the episode is not canon
    FILLER = 3 # nothing related to the original support

@dataclass(frozen=True)
class FillerData:
    filler: FillerType
    absoluteNumber: int
