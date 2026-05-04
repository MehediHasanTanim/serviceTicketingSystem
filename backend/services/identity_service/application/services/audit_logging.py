from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class AuditContext:
    org_id: int
    property_id: Optional[int]
    actor_user_id: Optional[int]
    ip_address: str
    user_agent: str


class AuditLogger(Protocol):
    def log_action(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        context: AuditContext,
    ) -> None:
        ...

    def log_entity_change(
        self,
        *,
        entity_type: str,
        entity_id: str,
        change_type: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        context: AuditContext,
    ) -> None:
        ...
