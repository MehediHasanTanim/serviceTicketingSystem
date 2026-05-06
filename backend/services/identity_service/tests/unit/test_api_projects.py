import pytest
from django.urls import reverse
from rest_framework import status

from infrastructure.db.core.models import AuditLog, Project, SnaggingItem
from tests.unit.api_test_helpers import authenticated_client, create_org, create_user, grant_permissions


@pytest.mark.django_db
@pytest.mark.unit
def test_projects_api_requires_permissions():
    org = create_org("Projects RBAC")
    actor = create_user(org, email="noperm@example.com")
    client = authenticated_client(actor)

    create_res = client.post(reverse("project-list-create"), {"org_id": org.id, "title": "No Perm"}, format="json")
    list_res = client.get(reverse("project-list-create"), {"org_id": org.id})
    assert create_res.status_code == status.HTTP_403_FORBIDDEN
    assert list_res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.unit
def test_project_crud_filters_pagination_status_progress_timeline_and_audit_logs():
    org = create_org("Projects Org")
    actor = create_user(org, email="pm-api@example.com")
    assignee = create_user(org, email="assignee-api@example.com")
    grant_permissions(actor, ["projects.view", "projects.manage", "audit.view"], role_name="project-manager")
    client = authenticated_client(actor)

    ids = []
    for idx in range(3):
        res = client.post(
            reverse("project-list-create"),
            {
                "org_id": org.id,
                "title": f"Project {idx}",
                "priority": "HIGH" if idx == 0 else "LOW",
                "project_type": "RENOVATION",
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        ids.append(res.data["id"])

    list_res = client.get(reverse("project-list-create"), {"org_id": org.id, "priority": "HIGH", "page": 1, "page_size": 1})
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.data["count"] == 1
    assert len(list_res.data["results"]) == 1

    patch_res = client.patch(
        reverse("project-detail", kwargs={"project_id": ids[0]}),
        {"org_id": org.id, "title": "Project 0 Updated", "progress_percentage": 10},
        format="json",
    )
    assert patch_res.status_code == status.HTTP_200_OK

    status_bad = client.post(
        reverse("project-status", kwargs={"project_id": ids[0]}),
        {"org_id": org.id, "new_status": "COMPLETED"},
        format="json",
    )
    assert status_bad.status_code == status.HTTP_400_BAD_REQUEST

    client.post(reverse("project-status", kwargs={"project_id": ids[0]}), {"org_id": org.id, "new_status": "PLANNED"}, format="json")
    client.post(reverse("project-status", kwargs={"project_id": ids[0]}), {"org_id": org.id, "new_status": "IN_PROGRESS"}, format="json")

    progress_res = client.post(
        reverse("project-progress", kwargs={"project_id": ids[0]}),
        {"org_id": org.id, "progress_percentage": 45},
        format="json",
    )
    assert progress_res.status_code == status.HTTP_200_OK

    snag_res = client.post(
        reverse("project-snagging-list-create", kwargs={"project_id": ids[0]}),
        {"org_id": org.id, "title": "Critical cable", "severity": "CRITICAL"},
        format="json",
    )
    assert snag_res.status_code == status.HTTP_201_CREATED
    snag_id = snag_res.data["id"]

    block_complete = client.post(
        reverse("project-status", kwargs={"project_id": ids[0]}),
        {"org_id": org.id, "new_status": "COMPLETED", "actual_end_date": "2026-01-01"},
        format="json",
    )
    assert block_complete.status_code == status.HTTP_400_BAD_REQUEST

    assign_res = client.post(
        reverse("project-snagging-assign", kwargs={"snag_id": snag_id}),
        {"org_id": org.id, "assignee_id": assignee.id, "reason": "take ownership"},
        format="json",
    )
    assert assign_res.status_code == status.HTTP_200_OK
    client.post(reverse("project-snagging-start", kwargs={"snag_id": snag_id}), {"org_id": org.id}, format="json")
    client.post(reverse("project-snagging-resolve", kwargs={"snag_id": snag_id}), {"org_id": org.id}, format="json")

    done_res = client.post(
        reverse("project-status", kwargs={"project_id": ids[0]}),
        {"org_id": org.id, "new_status": "COMPLETED", "actual_end_date": "2026-01-01"},
        format="json",
    )
    assert done_res.status_code == status.HTTP_200_OK

    timeline_res = client.get(reverse("project-timeline", kwargs={"project_id": ids[0]}), {"org_id": org.id})
    assert timeline_res.status_code == status.HTTP_200_OK
    assert timeline_res.data["count"] > 0

    logs = AuditLog.objects.filter(org=org)
    actions = set(logs.values_list("action", flat=True))
    assert "project_created" in actions
    assert "project_status_changed" in actions
    assert "project_progress_updated" in actions
    assert "snagging_item_created" in actions
    assert "snagging_item_assigned" in actions


@pytest.mark.django_db
@pytest.mark.unit
def test_snagging_terminal_and_reason_rules_and_validation_errors():
    org = create_org("Projects Snag")
    actor = create_user(org, email="snag@example.com")
    grant_permissions(actor, ["projects.view", "projects.manage"], role_name="project-manager")
    client = authenticated_client(actor)

    project = client.post(reverse("project-list-create"), {"org_id": org.id, "title": "Snag proj"}, format="json").data
    snag = client.post(reverse("project-snagging-list-create", kwargs={"project_id": project["id"]}), {"org_id": org.id, "title": "Door alignment"}, format="json").data

    client.post(reverse("project-snagging-start", kwargs={"snag_id": snag["id"]}), {"org_id": org.id}, format="json")
    client.post(reverse("project-snagging-resolve", kwargs={"snag_id": snag["id"]}), {"org_id": org.id}, format="json")
    verify = client.post(reverse("project-snagging-verify", kwargs={"snag_id": snag["id"]}), {"org_id": org.id}, format="json")
    assert verify.status_code == status.HTTP_200_OK

    invalid_terminal = client.post(reverse("project-snagging-start", kwargs={"snag_id": snag["id"]}), {"org_id": org.id}, format="json")
    assert invalid_terminal.status_code == status.HTTP_400_BAD_REQUEST

    snag2 = client.post(reverse("project-snagging-list-create", kwargs={"project_id": project["id"]}), {"org_id": org.id, "title": "Crack"}, format="json").data
    reopen_fail = client.post(reverse("project-snagging-reopen", kwargs={"snag_id": snag2["id"]}), {"org_id": org.id}, format="json")
    assert reopen_fail.status_code == status.HTTP_400_BAD_REQUEST

    cancel_fail = client.post(reverse("project-snagging-cancel", kwargs={"snag_id": snag2["id"]}), {"org_id": org.id}, format="json")
    assert cancel_fail.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.unit
def test_technical_audit_api_workflow_and_failed_audit_corrective_item():
    org = create_org("Projects TA")
    actor = create_user(org, email="ta@example.com")
    grant_permissions(actor, ["projects.view", "projects.manage"], role_name="project-manager")
    client = authenticated_client(actor)

    project = client.post(reverse("project-list-create"), {"org_id": org.id, "title": "Audit proj"}, format="json").data

    created = client.post(
        reverse("project-technical-audit-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "title": "Initial audit"},
        format="json",
    )
    assert created.status_code == status.HTTP_201_CREATED
    audit_id = created.data["id"]

    started = client.post(reverse("project-technical-audit-start", kwargs={"audit_id": audit_id}), {"org_id": org.id}, format="json")
    assert started.status_code == status.HTTP_200_OK

    bad_score = client.post(
        reverse("project-technical-audit-complete", kwargs={"audit_id": audit_id}),
        {"org_id": org.id, "score": 120, "result": "FAIL"},
        format="json",
    )
    assert bad_score.status_code == status.HTTP_400_BAD_REQUEST

    completed = client.post(
        reverse("project-technical-audit-complete", kwargs={"audit_id": audit_id}),
        {"org_id": org.id, "score": 50, "result": "FAIL", "findings_summary": "bad", "auto_create_corrective_item": True},
        format="json",
    )
    assert completed.status_code == status.HTTP_200_OK

    assert SnaggingItem.objects.filter(project_id=project["id"], title__icontains="Corrective action").exists()
    assert Project.objects.get(id=project["id"]).timeline_entries.filter(event_type="technical_audit_completed").exists()

    actions = set(AuditLog.objects.filter(org=org).values_list("action", flat=True))
    assert "technical_audit_created" in actions
    assert "technical_audit_started" in actions
    assert "technical_audit_completed" in actions


@pytest.mark.django_db
@pytest.mark.unit
def test_snagging_list_supports_server_side_filters_sorting_and_pagination():
    org = create_org("Projects Snag Query")
    actor = create_user(org, email="snag-query@example.com")
    assignee = create_user(org, email="snag-assignee@example.com")
    grant_permissions(actor, ["projects.view", "projects.manage"], role_name="project-manager")
    client = authenticated_client(actor)

    project = client.post(reverse("project-list-create"), {"org_id": org.id, "title": "Snag Query Project"}, format="json").data

    s1 = client.post(
        reverse("project-snagging-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "title": "Critical Leak", "severity": "CRITICAL", "category": "PLUMBING", "assigned_to": assignee.id, "due_at": "2026-01-20T10:00:00Z"},
        format="json",
    )
    assert s1.status_code == status.HTTP_201_CREATED
    s2 = client.post(
        reverse("project-snagging-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "title": "Paint touchup", "severity": "LOW", "category": "FINISHING", "due_at": "2026-01-10T10:00:00Z"},
        format="json",
    )
    assert s2.status_code == status.HTTP_201_CREATED
    s3 = client.post(
        reverse("project-snagging-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "title": "Cable issue", "severity": "HIGH", "category": "ELECTRICAL", "due_at": "2026-01-15T10:00:00Z"},
        format="json",
    )
    assert s3.status_code == status.HTTP_201_CREATED

    client.post(reverse("project-snagging-start", kwargs={"snag_id": s3.data["id"]}), {"org_id": org.id}, format="json")

    filtered = client.get(
        reverse("project-snagging-list-create", kwargs={"project_id": project["id"]}),
        {
            "org_id": org.id,
            "q": "Leak",
            "severity": "CRITICAL",
            "category": "PLUMBING",
            "assigned_to": assignee.id,
            "due_from": "2026-01-19T00:00:00Z",
            "due_to": "2026-01-21T00:00:00Z",
            "sort_by": "due_at",
            "sort_dir": "asc",
            "page": 1,
            "page_size": 10,
        },
    )
    assert filtered.status_code == status.HTTP_200_OK
    assert filtered.data["count"] == 1
    assert filtered.data["results"][0]["title"] == "Critical Leak"
    assert filtered.data["page"] == 1
    assert filtered.data["page_size"] == 10

    paged = client.get(
        reverse("project-snagging-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "sort_by": "due_at", "sort_dir": "asc", "page": 2, "page_size": 1},
    )
    assert paged.status_code == status.HTTP_200_OK
    assert paged.data["count"] == 3
    assert len(paged.data["results"]) == 1
    assert paged.data["results"][0]["title"] == "Cable issue"


@pytest.mark.django_db
@pytest.mark.unit
def test_technical_audit_list_supports_server_side_filters_sorting_and_pagination():
    org = create_org("Projects Audit Query")
    actor = create_user(org, email="audit-query@example.com")
    auditor = create_user(org, email="auditor@example.com")
    grant_permissions(actor, ["projects.view", "projects.manage"], role_name="project-manager")
    client = authenticated_client(actor)

    project = client.post(reverse("project-list-create"), {"org_id": org.id, "title": "Audit Query Project"}, format="json").data

    a1 = client.post(
        reverse("project-technical-audit-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "title": "Electrical Audit", "auditor_id": auditor.id, "conducted_at": "2026-01-20T10:00:00Z"},
        format="json",
    )
    assert a1.status_code == status.HTTP_201_CREATED
    a2 = client.post(
        reverse("project-technical-audit-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "title": "HVAC Audit", "auditor_id": auditor.id, "conducted_at": "2026-01-10T10:00:00Z"},
        format="json",
    )
    assert a2.status_code == status.HTTP_201_CREATED
    a3 = client.post(
        reverse("project-technical-audit-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "title": "Plumbing Audit"},
        format="json",
    )
    assert a3.status_code == status.HTTP_201_CREATED

    client.post(reverse("project-technical-audit-start", kwargs={"audit_id": a1.data["id"]}), {"org_id": org.id}, format="json")
    client.post(
        reverse("project-technical-audit-complete", kwargs={"audit_id": a1.data["id"]}),
        {"org_id": org.id, "result": "PASS", "score": 91},
        format="json",
    )

    filtered = client.get(
        reverse("project-technical-audit-list-create", kwargs={"project_id": project["id"]}),
        {
            "org_id": org.id,
            "q": "Electrical",
            "status": "COMPLETED",
            "result": "PASS",
            "auditor": auditor.id,
            "conducted_from": "2026-01-19T00:00:00Z",
            "conducted_to": "2026-01-21T00:00:00Z",
            "sort_by": "conducted_at",
            "sort_dir": "desc",
            "page": 1,
            "page_size": 10,
        },
    )
    assert filtered.status_code == status.HTTP_200_OK
    assert filtered.data["count"] == 1
    assert filtered.data["results"][0]["title"] == "Electrical Audit"
    assert filtered.data["page"] == 1
    assert filtered.data["page_size"] == 10

    paged = client.get(
        reverse("project-technical-audit-list-create", kwargs={"project_id": project["id"]}),
        {"org_id": org.id, "sort_by": "conducted_at", "sort_dir": "asc", "page": 2, "page_size": 1},
    )
    assert paged.status_code == status.HTTP_200_OK
    assert paged.data["count"] == 3
    assert len(paged.data["results"]) == 1
