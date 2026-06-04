from abc import ABC, abstractmethod
from typing import Any, Optional

class ICache(ABC):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass