import pytest

from application.services.projects import (
    ProjectLifecycleValidator,
    ProjectLifecycleService,
    ProjectService,
    ProjectTransitionError,
    ProjectValidationError,
    SnaggingItemService,
    SnaggingTransitionError,
    TechnicalAuditService,
)
from infrastructure.db.core.models import Project, SnaggingItem, SnaggingItemAssignmentHistory, SnaggingItemStatusHistory, TechnicalAudit
from tests.unit.api_test_helpers import create_org, create_user


@pytest.mark.django_db
@pytest.mark.unit
def test_project_status_transition_rules_and_terminal_states():
    v = ProjectLifecycleValidator()
    v.validate(Project.STATUS_DRAFT, Project.STATUS_PLANNED)
    with pytest.raises(ProjectTransitionError):
        v.validate(Project.STATUS_DRAFT, Project.STATUS_COMPLETED)
    with pytest.raises(ProjectTransitionError):
        v.validate(Project.STATUS_COMPLETED, Project.STATUS_IN_PROGRESS)


@pytest.mark.django_db
@pytest.mark.unit
def test_project_completion_requires_actual_end_date_and_no_blocking_critical_snag():
    org = create_org("Proj Org")
    actor = create_user(org, email="owner@example.com")
    project_service = ProjectService()
    lifecycle = ProjectLifecycleService()
    snag_service = SnaggingItemService()

    project = project_service.create(org_id=org.id, actor=actor, title="Tower Upgrade")
    project = lifecycle.change_status(project=project, to_status=Project.STATUS_PLANNED, actor=actor)
    project = lifecycle.change_status(project=project, to_status=Project.STATUS_IN_PROGRESS, actor=actor)

    with pytest.raises(ProjectValidationError):
        lifecycle.change_status(project=project, to_status=Project.STATUS_COMPLETED, actor=actor)

    critical = snag_service.create(project=project, actor=actor, title="Critical leak", severity=SnaggingItem.SEVERITY_CRITICAL)
    with pytest.raises(ProjectValidationError):
        lifecycle.change_status(project=project, to_status=Project.STATUS_COMPLETED, actor=actor, actual_end_date=project.created_at.date())

    snag_service.transition(snag=critical, to_status=SnaggingItem.STATUS_IN_PROGRESS, actor=actor)
    snag_service.transition(snag=critical, to_status=SnaggingItem.STATUS_RESOLVED, actor=actor)
    completed = lifecycle.change_status(project=project, to_status=Project.STATUS_COMPLETED, actor=actor, actual_end_date=project.created_at.date())
    assert completed.status == Project.STATUS_COMPLETED


@pytest.mark.django_db
@pytest.mark.unit
def test_project_progress_validation_and_timeline_created():
    org = create_org("Proj Org")
    actor = create_user(org, email="pm@example.com")
    project_service = ProjectService()
    lifecycle = ProjectLifecycleService()
    project = project_service.create(org_id=org.id, actor=actor, title="Lobby refresh")

    lifecycle.update_progress(project=project, progress_percentage=45, actor=actor)
    project.refresh_from_db()
    assert project.progress_percentage == 45
    assert project.timeline_entries.filter(event_type="project_progress_updated").exists()

    with pytest.raises(ProjectValidationError):
        lifecycle.update_progress(project=project, progress_percentage=120, actor=actor)


@pytest.mark.django_db
@pytest.mark.unit
def test_snagging_workflow_transitions_history_and_reasons():
    org = create_org("Proj Org")
    actor = create_user(org, email="pm2@example.com")
    assignee = create_user(org, email="tech@example.com")
    project = ProjectService().create(org_id=org.id, actor=actor, title="Kitchen fitout")
    service = SnaggingItemService()

    snag = service.create(project=project, actor=actor, title="Broken tile")
    service.assign(snag=snag, assignee=assignee, actor=actor, reason="ownership")
    service.transition(snag=snag, to_status=SnaggingItem.STATUS_IN_PROGRESS, actor=actor)
    service.transition(snag=snag, to_status=SnaggingItem.STATUS_RESOLVED, actor=actor)
    service.transition(snag=snag, to_status=SnaggingItem.STATUS_VERIFIED, actor=actor)
    assert SnaggingItemAssignmentHistory.objects.filter(snagging_item=snag).count() == 1
    assert SnaggingItemStatusHistory.objects.filter(snagging_item=snag).count() >= 4

    with pytest.raises(SnaggingTransitionError):
        service.transition(snag=snag, to_status=SnaggingItem.STATUS_IN_PROGRESS, actor=actor)

    snag2 = service.create(project=project, actor=actor, title="Paint peel")
    service.transition(snag=snag2, to_status=SnaggingItem.STATUS_IN_PROGRESS, actor=actor)
    service.transition(snag=snag2, to_status=SnaggingItem.STATUS_RESOLVED, actor=actor)
    with pytest.raises(ProjectValidationError):
        service.transition(snag=snag2, to_status=SnaggingItem.STATUS_REOPENED, actor=actor)
    reopened = service.transition(snag=snag2, to_status=SnaggingItem.STATUS_REOPENED, actor=actor, reason="recheck failed")
    assert reopened.status == SnaggingItem.STATUS_REOPENED


@pytest.mark.django_db
@pytest.mark.unit
def test_technical_audit_workflow_and_failed_audit_can_create_corrective_item():
    org = create_org("Proj Org")
    actor = create_user(org, email="auditor@example.com")
    project = ProjectService().create(org_id=org.id, actor=actor, title="Fire system project")
    service = TechnicalAuditService()

    audit = service.create(project=project, actor=actor, title="Stage-1 Audit")
    started = service.transition(audit=audit, to_status=TechnicalAudit.STATUS_IN_PROGRESS, actor=actor)
    assert started.status == TechnicalAudit.STATUS_IN_PROGRESS

    with pytest.raises(ProjectValidationError):
        service.transition(audit=audit, to_status=TechnicalAudit.STATUS_COMPLETED, actor=actor, score=130)

    completed = service.transition(
        audit=audit,
        to_status=TechnicalAudit.STATUS_COMPLETED,
        actor=actor,
        result=TechnicalAudit.RESULT_FAIL,
        score=55,
        findings_summary="Major defects",
        auto_create_corrective_item=True,
    )
    assert completed.status == TechnicalAudit.STATUS_COMPLETED
    assert completed.project.snagging_items.filter(title__icontains="Corrective action").exists()
    assert project.timeline_entries.filter(event_type="technical_audit_completed").exists()
