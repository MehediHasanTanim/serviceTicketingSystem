from typing import Any, Dict, Optional

from application.services.audit_logging import AuditContext, AuditLogger
from infrastructure.db.core.models import AuditLog, EntityHistory, Organization, Property, User


class DjangoAuditLogger(AuditLogger):
    def _resolve_org(self, org_id: int):
        return Organization.objects.filter(id=org_id).first()

    def _resolve_property(self, property_id: Optional[int]):
        if not property_id:
            return None
        return Property.objects.filter(id=property_id).first()

    def _resolve_actor(self, user_id: Optional[int]):
        if not user_id:
            return None
        return User.objects.filter(id=user_id).first()

    def log_action(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        context: AuditContext,
    ) -> None:
        org = self._resolve_org(context.org_id)
        if not org:
            return
        AuditLog.objects.create(
            org=org,
            property=self._resolve_property(context.property_id),
            actor_user=self._resolve_actor(context.actor_user_id),
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata_json=metadata or {},
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )

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
        org = self._resolve_org(context.org_id)
        if not org:
            return
        EntityHistory.objects.create(
            org=org,
            property=self._resolve_property(context.property_id),
            actor_user=self._resolve_actor(context.actor_user_id),
            entity_type=entity_type,
            entity_id=str(entity_id),
            change_type=change_type,
            before_json=before or {},
            after_json=after or {},
        )


_AUDIT_LOGGER = DjangoAuditLogger()


def get_audit_logger() -> AuditLogger:
    return _AUDIT_LOGGER
