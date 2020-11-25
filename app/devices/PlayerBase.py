from abc import ABC, abstractmethod


class PlayerBase(ABC):
    @abstractmethod
    def __init__(
        self,
        token: str,
        address: str,
        port: int = None,
        user: str = None,
        password: str = None,
        device: str = None,
    ):
        pass

    @abstractmethod
    def playMedia(self, obj):
        pass

    @abstractmethod
    def stop(self):
        pass