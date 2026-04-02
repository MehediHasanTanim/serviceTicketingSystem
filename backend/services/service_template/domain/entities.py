from dataclasses import dataclass


@dataclass(frozen=True)
class EntityId:
    value: str


@dataclass
class BaseEntity:
    id: EntityId
