from infrastructure.db.core.models import AuditLog


def assert_transition(response, expected_status: str) -> None:
    assert response.status_code == 200
    payload = response.data.get("data", response.data)
    assert payload["status"] == expected_status


def assert_audit_recorded(*, action: str, target_type: str | None = None, target_id: str | None = None) -> None:
    filters = {"action": action}
    if target_type is not None:
        filters["target_type"] = target_type
    if target_id is not None:
        filters["target_id"] = str(target_id)
    assert AuditLog.objects.filter(**filters).exists()
