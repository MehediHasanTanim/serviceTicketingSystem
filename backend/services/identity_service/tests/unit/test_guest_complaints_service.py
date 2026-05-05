from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from application.services.guest_complaints import (
    ComplaintFilters,
    ComplaintLifecycleService,
    ComplaintLifecycleValidator,
    ComplaintRoutingService,
    ComplaintService,
    GuestComplaintTransitionError,
    GuestComplaintValidationError,
    GuestExperienceAnalyticsService,
    ResolutionConfirmationService,
)
from infrastructure.db.core.models import Department, GuestComplaint, GuestComplaintEscalation, GuestComplaintFollowUp, GuestComplaintRoutingRule, GuestComplaintStatusHistory
from tests.unit.api_test_helpers import create_org, create_user


@pytest.mark.django_db
@pytest.mark.unit
def test_lifecycle_transitions_and_terminal_rules_and_history():
    validator = ComplaintLifecycleValidator()
    validator.validate(GuestComplaint.STATUS_NEW, GuestComplaint.STATUS_TRIAGED)
    with pytest.raises(GuestComplaintTransitionError):
        validator.validate(GuestComplaint.STATUS_NEW, GuestComplaint.STATUS_CONFIRMED)
    with pytest.raises(GuestComplaintTransitionError):
        validator.validate(GuestComplaint.STATUS_CLOSED, GuestComplaint.STATUS_ASSIGNED)
    with pytest.raises(GuestComplaintTransitionError):
        validator.validate(GuestComplaint.STATUS_VOID, GuestComplaint.STATUS_ASSIGNED)
    with pytest.raises(GuestComplaintTransitionError):
        validator.validate(GuestComplaint.STATUS_RESOLVED, GuestComplaint.STATUS_REOPENED, reason="")
    with pytest.raises(GuestComplaintTransitionError):
        validator.validate(GuestComplaint.STATUS_ASSIGNED, GuestComplaint.STATUS_VOID, reason="")

    org = create_org("Complaints Org")
    actor = create_user(org, email="actor@example.com")
    complaint = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000001",
        guest_name="A Guest",
        property=org.properties.create(code="P1", name="Prop", timezone="UTC", address_line1="x", city="x", country="x"),
        category=GuestComplaint.CATEGORY_MAINTENANCE,
        severity=GuestComplaint.SEVERITY_MEDIUM,
        status=GuestComplaint.STATUS_NEW,
        title="Noise",
        source=GuestComplaint.SOURCE_PHONE,
        created_by=actor,
        updated_by=actor,
    )
    service = ComplaintLifecycleService()
    service.transition(complaint=complaint, to_status=GuestComplaint.STATUS_TRIAGED, actor=actor)
    assert GuestComplaintStatusHistory.objects.filter(complaint=complaint).count() == 1


@pytest.mark.django_db
@pytest.mark.unit
def test_routing_rules_and_default_queue_and_metadata():
    org = create_org("Routing Org")
    actor = create_user(org, email="routing@example.com")
    prop = org.properties.create(code="P2", name="Prop2", timezone="UTC", address_line1="x", city="x", country="x")
    hk = Department.objects.create(org=org, property=prop, name="Housekeeping", description="")
    gr = Department.objects.create(org=org, property=prop, name="Guest Relations", description="")

    c1 = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000002",
        guest_name="G",
        property=prop,
        category=GuestComplaint.CATEGORY_ROOM_CLEANLINESS,
        severity=GuestComplaint.SEVERITY_HIGH,
        status=GuestComplaint.STATUS_NEW,
        title="Dirty room",
        source=GuestComplaint.SOURCE_FRONT_DESK,
        created_by=actor,
        updated_by=actor,
    )
    route = ComplaintRoutingService().route(complaint=c1)
    c1.refresh_from_db()
    assert c1.department_id == hk.id
    assert route["fallback"] is False

    c2 = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000003",
        guest_name="G2",
        property=prop,
        category=GuestComplaint.CATEGORY_OTHER,
        severity=GuestComplaint.SEVERITY_MEDIUM,
        status=GuestComplaint.STATUS_NEW,
        title="Other",
        source=GuestComplaint.SOURCE_FRONT_DESK,
        created_by=actor,
        updated_by=actor,
    )
    route2 = ComplaintRoutingService().route(complaint=c2)
    assert route2["fallback"] is True


@pytest.mark.django_db
@pytest.mark.unit
def test_vip_and_shift_routing_rule_is_applied():
    org = create_org("Routing Rule Org")
    actor = create_user(org, email="rule@example.com")
    assignee = create_user(org, email="rule.assignee@example.com")
    prop = org.properties.create(code="PR", name="PropR", timezone="UTC", address_line1="x", city="x", country="x")
    security = Department.objects.create(org=org, property=prop, name="Security", description="")
    Department.objects.create(org=org, property=prop, name="Guest Relations", description="")

    GuestComplaintRoutingRule.objects.create(
        category=GuestComplaint.CATEGORY_SAFETY_SECURITY,
        severity=GuestComplaint.SEVERITY_HIGH,
        property=prop,
        shift=GuestComplaint.SHIFT_NIGHT,
        vip_only=True,
        department=security,
        assign_to=assignee,
        priority=1,
        is_active=True,
    )
    complaint = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000008",
        guest_name="VIP Guest",
        property=prop,
        category=GuestComplaint.CATEGORY_SAFETY_SECURITY,
        severity=GuestComplaint.SEVERITY_HIGH,
        status=GuestComplaint.STATUS_NEW,
        title="Safety concern",
        source=GuestComplaint.SOURCE_PHONE,
        vip_guest=True,
        shift=GuestComplaint.SHIFT_NIGHT,
        created_by=actor,
        updated_by=actor,
    )
    meta = ComplaintRoutingService().route(complaint=complaint, vip_guest=True)
    complaint.refresh_from_db()
    assert meta["fallback"] is False
    assert meta["rule_id"] is not None
    assert complaint.department_id == security.id
    assert complaint.assigned_to_id == assignee.id


@pytest.mark.django_db
@pytest.mark.unit
def test_escalation_rules_critical_overdue_duplicate_and_batch_summary():
    org = create_org("Escalation Org")
    actor = create_user(org, email="esc@example.com")
    prop = org.properties.create(code="P3", name="Prop3", timezone="UTC", address_line1="x", city="x", country="x")
    service = ComplaintService()

    critical, _ = service.create(
        created_by=actor,
        org_id=org.id,
        guest_name="Critical",
        property_id=prop.id,
        category=GuestComplaint.CATEGORY_SAFETY_SECURITY,
        severity=GuestComplaint.SEVERITY_CRITICAL,
        title="Critical issue",
        source=GuestComplaint.SOURCE_PHONE,
    )
    assert GuestComplaintEscalation.objects.filter(complaint=critical).count() >= 1

    overdue = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000004",
        guest_name="Overdue",
        property=prop,
        category=GuestComplaint.CATEGORY_MAINTENANCE,
        severity=GuestComplaint.SEVERITY_HIGH,
        status=GuestComplaint.STATUS_ASSIGNED,
        title="Overdue issue",
        source=GuestComplaint.SOURCE_PHONE,
        due_at=timezone.now() - timedelta(hours=2),
        created_by=actor,
        updated_by=actor,
    )

    done1, _ = service.escalation_service.escalate(complaint=overdue, actor=actor, reason="manual", escalation_level=1, manual=True)
    done2, flag2 = service.escalation_service.escalate(complaint=overdue, actor=actor, reason="manual", escalation_level=1, manual=True)
    assert done1 is True
    assert done2 is False
    assert flag2 == "duplicate_active_escalation"

    summary = service.escalation_service.run_batch(org_id=org.id, actor=actor)
    assert summary["checked_count"] >= 2
    assert "escalated_count" in summary


@pytest.mark.django_db
@pytest.mark.unit
def test_follow_up_creation_completion_missed_and_filters():
    org = create_org("Followup Org")
    actor = create_user(org, email="fu@example.com")
    prop = org.properties.create(code="P4", name="Prop4", timezone="UTC", address_line1="x", city="x", country="x")
    complaint = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000005",
        guest_name="FU",
        property=prop,
        category=GuestComplaint.CATEGORY_MAINTENANCE,
        severity=GuestComplaint.SEVERITY_HIGH,
        status=GuestComplaint.STATUS_RESOLVED,
        title="Resolved",
        source=GuestComplaint.SOURCE_PHONE,
        created_by=actor,
        updated_by=actor,
    )
    fu_service = ComplaintService().follow_up_service
    follow_up = fu_service.create_follow_up(
        complaint=complaint,
        follow_up_type="POST_RESOLUTION",
        scheduled_at=timezone.now() - timedelta(hours=1),
        created_by=actor,
        assigned_to=actor,
    )
    assert follow_up.status == GuestComplaintFollowUp.STATUS_PENDING
    fu_service.mark_missed(now=timezone.now())
    follow_up.refresh_from_db()
    assert follow_up.status == GuestComplaintFollowUp.STATUS_MISSED

    follow_up2 = fu_service.create_follow_up(
        complaint=complaint,
        follow_up_type="MANUAL",
        scheduled_at=timezone.now() + timedelta(hours=5),
        created_by=actor,
        assigned_to=actor,
    )
    fu_service.complete_follow_up(follow_up=follow_up2, notes="done")
    follow_up2.refresh_from_db()
    assert follow_up2.status == GuestComplaintFollowUp.STATUS_COMPLETED

    listed = fu_service.repository.list(complaint_id=complaint.id, assigned_to=actor.id, status=GuestComplaintFollowUp.STATUS_COMPLETED)
    assert listed.count() == 1


@pytest.mark.django_db
@pytest.mark.unit
def test_resolution_confirmation_and_low_satisfaction_reopen_and_analytics_zero_safe():
    org = create_org("Confirm Org")
    actor = create_user(org, email="confirm@example.com")
    prop = org.properties.create(code="P5", name="Prop5", timezone="UTC", address_line1="x", city="x", country="x")
    complaint = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000006",
        guest_name="Confirm",
        property=prop,
        category=GuestComplaint.CATEGORY_BILLING,
        severity=GuestComplaint.SEVERITY_MEDIUM,
        status=GuestComplaint.STATUS_RESOLVED,
        title="Billing",
        source=GuestComplaint.SOURCE_EMAIL,
        created_by=actor,
        updated_by=actor,
    )

    confirmation = ResolutionConfirmationService()
    updated = confirmation.confirm(
        complaint=complaint,
        actor=actor,
        satisfaction_score=Decimal("1.00"),
        satisfaction_comment="not good",
    )
    updated.refresh_from_db()
    assert updated.satisfaction_score == Decimal("1.00")
    assert updated.status == GuestComplaint.STATUS_REOPENED

    unresolved = GuestComplaint.objects.create(
        org=org,
        complaint_number="GC-00000007",
        guest_name="U",
        property=prop,
        category=GuestComplaint.CATEGORY_NOISE,
        severity=GuestComplaint.SEVERITY_LOW,
        status=GuestComplaint.STATUS_NEW,
        title="Noise",
        source=GuestComplaint.SOURCE_PHONE,
        created_by=actor,
        updated_by=actor,
    )
    with pytest.raises(GuestComplaintValidationError):
        confirmation.confirm(complaint=unresolved, actor=actor, satisfaction_score=3)

    analytics = GuestExperienceAnalyticsService()
    empty_org = create_org("Empty Analytics")
    summary = analytics.summary(org_id=empty_org.id, filters=ComplaintFilters(org_id=empty_org.id))
    assert summary["total_complaints"] == 0
    sat = analytics.satisfaction(org_id=empty_org.id, filters=ComplaintFilters(org_id=empty_org.id))
    assert sat["average_satisfaction_score"] == 0.0
