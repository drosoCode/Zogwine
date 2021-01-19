from abc import ABC, abstractmethod


class PlayerBase(ABC):
    @abstractmethod
    def __init__(
        self,
        uid: int,
        token: str,
        address: str,
        port: int = None,
        user: str = None,
        password: str = None,
        device: str = None,
    ):
        pass

    @abstractmethod
    def playMedia(self, mediaType: int, mediaData: int, data: dict = None):
        pass

    @abstractmethod
    def stop(self):
        pass