from dataclasses import dataclass
from enum import IntEnum

VIDEO_FILES = ["mkv", "mp4", "avi"]


class ConfigEntryType(IntEnum):
    INT = 0
    FLOAT = 1
    STR = 2


@dataclass(frozen=True)
class ConfigEntry:
    name: str
    default: str
    required: bool
    type: ConfigEntryType
    values: list
    min: int
    max: int
    multiple: bool


class MediaType(IntEnum):
    TVS_EPISODE = 1
    TVS = 2
    MOVIE = 3