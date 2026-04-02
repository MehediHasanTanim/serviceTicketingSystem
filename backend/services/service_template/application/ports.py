from abc import ABC, abstractmethod


class Repository(ABC):
    """Generic repository interface."""

    @abstractmethod
    def add(self, entity):
        raise NotImplementedError

    @abstractmethod
    def get(self, entity_id):
        raise NotImplementedError

    @abstractmethod
    def list(self, **filters):
        raise NotImplementedError
