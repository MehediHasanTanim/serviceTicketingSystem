from decimal import Decimal

import pytest
from django.utils import timezone

from application.services.inspections import (
    InspectionEventPublisher,
    InspectionExecutionService,
    InspectionScoringService,
    InspectionValidationError,
)
from infrastructure.db.core.models import (
    InspectionChecklistItem,
    InspectionChecklistSection,
    InspectionRun,
    InspectionStepResponse,
    InspectionTemplate,
    NonComplianceAlert,
)
from tests.unit.api_test_helpers import create_org, create_user


@pytest.fixture
def inspection_setup(db):
    org = create_org("Inspection Org")
    actor = create_user(org, email="inspector@example.com")
    template = InspectionTemplate.objects.create(
        org=org,
        template_code="TPL-001",
        name="Room Inspection",
        description="",
        category="ROOM",
        is_active=True,
        version=1,
        created_by=actor,
        updated_by=actor,
    )
    section = InspectionChecklistSection.objects.create(
        template=template,
        title="Safety",
        description="",
        sort_order=1,
        weight=Decimal("1.00"),
    )
    item_required = InspectionChecklistItem.objects.create(
        section=section,
        question="Door lock works",
        response_type=InspectionChecklistItem.RESPONSE_TYPE_PASS_FAIL_NA,
        is_required=True,
        weight=Decimal("3.00"),
        sort_order=1,
        non_compliance_trigger=True,
    )
    item_optional = InspectionChecklistItem.objects.create(
        section=section,
        question="Lights work",
        response_type=InspectionChecklistItem.RESPONSE_TYPE_PASS_FAIL_NA,
        is_required=False,
        weight=Decimal("1.00"),
        sort_order=2,
        non_compliance_trigger=False,
    )
    return org, actor, template, item_required, item_optional


def _create_run(org, actor, template):
    return InspectionRun.objects.create(
        org=org,
        inspection_number=f"INSP-{timezone.now().timestamp()}",
        template=template,
        status=InspectionRun.STATUS_IN_PROGRESS,
        result=InspectionRun.RESULT_PARTIAL,
        created_by=actor,
    )


def test_scoring_pass_fail_na_and_weighted_final(inspection_setup):
    org, actor, template, item_required, item_optional = inspection_setup
    run = _create_run(org, actor, template)

    InspectionStepResponse.objects.create(
        inspection_run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_PASS,
        score=item_required.weight,
        responded_by=actor,
    )
    InspectionStepResponse.objects.create(
        inspection_run=run,
        checklist_item=item_optional,
        response=InspectionStepResponse.RESPONSE_NA,
        score=Decimal("0"),
        responded_by=actor,
    )

    scoring = InspectionScoringService(pass_threshold=Decimal("90"))
    score, result, details = scoring.calculate_run_score(run=run)

    assert score == Decimal("100.00")
    assert result == InspectionRun.RESULT_PASS
    assert details["applicable_items"] == 1


def test_scoring_fail_returns_zero_and_fail_result(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    run = _create_run(org, actor, template)
    InspectionStepResponse.objects.create(
        inspection_run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_FAIL,
        score=Decimal("0"),
        comment="critical issue",
        evidence_attachment_id=123,
        responded_by=actor,
    )

    score, result, _ = InspectionScoringService(pass_threshold=Decimal("90")).calculate_run_score(run=run)
    assert score == Decimal("0.00")
    assert result == InspectionRun.RESULT_FAIL


def test_scoring_all_na_returns_not_applicable(inspection_setup):
    org, actor, template, item_required, item_optional = inspection_setup
    run = _create_run(org, actor, template)
    for item in [item_required, item_optional]:
        InspectionStepResponse.objects.create(
            inspection_run=run,
            checklist_item=item,
            response=InspectionStepResponse.RESPONSE_NA,
            score=Decimal("0"),
            responded_by=actor,
        )
    score, result, _ = InspectionScoringService().calculate_run_score(run=run)
    assert score == Decimal("0")
    assert result == InspectionRun.RESULT_NOT_APPLICABLE


def test_validation_fail_requires_comment_and_evidence(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    service = InspectionExecutionService()
    run = _create_run(org, actor, template)

    with pytest.raises(InspectionValidationError):
        service.submit_response(
            run=run,
            checklist_item=item_required,
            response=InspectionStepResponse.RESPONSE_FAIL,
            comment="",
            evidence_attachment_id=None,
            actor=actor,
        )


def test_cannot_complete_without_start(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    service = InspectionExecutionService()
    run = InspectionRun.objects.create(
        org=org,
        inspection_number=f"INSP-{timezone.now().timestamp()}",
        template=template,
        status=InspectionRun.STATUS_SCHEDULED,
        result=InspectionRun.RESULT_PARTIAL,
        created_by=actor,
    )
    with pytest.raises(InspectionValidationError):
        service.complete_run(run=run, actor=actor)


def test_required_item_must_be_answered_before_completion(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    service = InspectionExecutionService()
    run = _create_run(org, actor, template)
    with pytest.raises(InspectionValidationError):
        service.complete_run(run=run, actor=actor)


def test_run_lifecycle_complete_sets_fields_and_terminal_state(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    service = InspectionExecutionService()
    run = InspectionRun.objects.create(
        org=org,
        inspection_number=f"INSP-{timezone.now().timestamp()}",
        template=template,
        status=InspectionRun.STATUS_SCHEDULED,
        result=InspectionRun.RESULT_PARTIAL,
        created_by=actor,
    )
    run = service.start_run(run=run, actor=actor)
    assert run.status == InspectionRun.STATUS_IN_PROGRESS
    assert run.started_at is not None

    service.submit_response(
        run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_PASS,
        comment="ok",
        evidence_attachment_id=None,
        actor=actor,
    )
    run, _ = service.complete_run(run=run, actor=actor)
    assert run.status == InspectionRun.STATUS_COMPLETED
    assert run.completed_at is not None
    assert run.final_score == Decimal("100.00")

    with pytest.raises(InspectionValidationError):
        service.submit_response(
            run=run,
            checklist_item=item_required,
            response=InspectionStepResponse.RESPONSE_PASS,
            comment="later",
            evidence_attachment_id=None,
            actor=actor,
        )


def test_non_compliance_alert_trigger_and_duplicate_prevention(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    service = InspectionExecutionService()
    run = _create_run(org, actor, template)

    _, _, _, alerts1 = service.submit_response(
        run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_FAIL,
        comment="failed",
        evidence_attachment_id=1,
        actor=actor,
    )
    _, _, _, alerts2 = service.submit_response(
        run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_FAIL,
        comment="failed again",
        evidence_attachment_id=2,
        actor=actor,
    )

    assert len(alerts1) == 1
    assert len(alerts2) == 0
    assert NonComplianceAlert.objects.filter(inspection_run=run, checklist_item=item_required).count() == 1


class _PublisherSpy(InspectionEventPublisher):
    def __init__(self, *, fail_on_alert: bool = False):
        self.fail_on_alert = fail_on_alert
        self.alert_calls = 0
        self.completed_calls = 0

    def publish_non_compliance_alert(self, *, alert):
        self.alert_calls += 1
        if self.fail_on_alert:
            raise RuntimeError("publisher down")

    def publish_inspection_completed(self, *, run):
        self.completed_calls += 1


def test_notification_hook_called_and_failure_non_blocking(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    publisher = _PublisherSpy(fail_on_alert=True)
    service = InspectionExecutionService(event_publisher=publisher)
    run = _create_run(org, actor, template)

    _, _, _, alerts = service.submit_response(
        run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_FAIL,
        comment="failed",
        evidence_attachment_id=1,
        actor=actor,
    )
    assert len(alerts) == 1
    assert publisher.alert_calls == 1


def test_completed_run_can_be_modified_with_admin_override(inspection_setup):
    org, actor, template, item_required, _ = inspection_setup
    service = InspectionExecutionService()
    run = _create_run(org, actor, template)

    service.submit_response(
        run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_PASS,
        comment="ok",
        evidence_attachment_id=None,
        actor=actor,
    )
    run, _ = service.complete_run(run=run, actor=actor)
    assert run.status == InspectionRun.STATUS_COMPLETED

    service.submit_response(
        run=run,
        checklist_item=item_required,
        response=InspectionStepResponse.RESPONSE_FAIL,
        comment="override update",
        evidence_attachment_id=99,
        actor=actor,
        admin_override=True,
    )
    run.refresh_from_db()
    assert run.status == InspectionRun.STATUS_IN_PROGRESS
