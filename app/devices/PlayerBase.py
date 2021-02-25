from abc import ABC, abstractmethod
from app.utils import ping


class PlayerBase(ABC):
    def __init__(
        self,
        uid: int,
        token: str,
        address: str,
        port: int = None,
        user: str = None,
        password: str = None,
        device: str = None,
        skipInit: bool = False,
    ):
        self._address = address

    @abstractmethod
    def playMedia(self, mediaType: int, mediaData: int, data: dict = None) -> tuple:
        # returns (device data, transcoder data)
        pass

    @abstractmethod
    def stop(self):
        pass

    @property
    def available(self) -> bool:
        ping(self._address)