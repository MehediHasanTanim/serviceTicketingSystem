from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Avg, Count, Q, QuerySet
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone

from infrastructure.db.core.models import (
    InspectionChecklistItem,
    InspectionChecklistSection,
    InspectionRun,
    InspectionRunHistory,
    InspectionStepResponse,
    InspectionTemplate,
    NonComplianceAlert,
    User,
)


class InspectionError(Exception):
    pass


class InspectionValidationError(InspectionError):
    pass


class InspectionNotFoundError(InspectionError):
    pass


class InspectionEventPublisher:
    def publish_non_compliance_alert(self, *, alert: NonComplianceAlert) -> None:
        return None

    def publish_inspection_completed(self, *, run: InspectionRun) -> None:
        return None


@dataclass
class InspectionRunFilters:
    org_id: int
    template_id: int | None = None
    status: str | None = None
    result: str | None = None
    property_id: int | None = None
    department_id: int | None = None
    location_id: int | None = None
    room_id: int | None = None
    asset_id: int | None = None
    assigned_to: int | None = None
    inspected_by: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class InspectionTemplateRepository:
    def create(self, **kwargs) -> InspectionTemplate:
        return InspectionTemplate.objects.create(**kwargs)

    def list(self, *, org_id: int, is_active: bool | None = None) -> QuerySet[InspectionTemplate]:
        qs = InspectionTemplate.objects.filter(org_id=org_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    def get_for_org(self, *, org_id: int, template_id: int) -> InspectionTemplate:
        try:
            return InspectionTemplate.objects.get(org_id=org_id, id=template_id)
        except InspectionTemplate.DoesNotExist as exc:
            raise InspectionNotFoundError("Inspection template not found") from exc


class InspectionSectionRepository:
    def create(self, **kwargs) -> InspectionChecklistSection:
        return InspectionChecklistSection.objects.create(**kwargs)


class InspectionItemRepository:
    def create(self, **kwargs) -> InspectionChecklistItem:
        return InspectionChecklistItem.objects.create(**kwargs)


class InspectionRunRepository:
    def create(self, **kwargs) -> InspectionRun:
        return InspectionRun.objects.create(**kwargs)

    def get_for_org(self, *, org_id: int, run_id: int) -> InspectionRun:
        try:
            return InspectionRun.objects.get(org_id=org_id, id=run_id)
        except InspectionRun.DoesNotExist as exc:
            raise InspectionNotFoundError("Inspection run not found") from exc

    def list(self, filters: InspectionRunFilters) -> QuerySet[InspectionRun]:
        qs = InspectionRun.objects.filter(org_id=filters.org_id)
        if filters.template_id:
            qs = qs.filter(template_id=filters.template_id)
        if filters.status:
            qs = qs.filter(status=filters.status)
        if filters.result:
            qs = qs.filter(result=filters.result)
        if filters.property_id:
            qs = qs.filter(property_id=filters.property_id)
        if filters.department_id:
            qs = qs.filter(department_id=filters.department_id)
        if filters.location_id:
            qs = qs.filter(location_id=filters.location_id)
        if filters.room_id:
            qs = qs.filter(room_id=filters.room_id)
        if filters.asset_id:
            qs = qs.filter(asset_id=filters.asset_id)
        if filters.assigned_to:
            qs = qs.filter(assigned_to_id=filters.assigned_to)
        if filters.inspected_by:
            qs = qs.filter(inspected_by_id=filters.inspected_by)
        if filters.date_from:
            qs = qs.filter(created_at__gte=filters.date_from)
        if filters.date_to:
            qs = qs.filter(created_at__lte=filters.date_to)
        return qs


class InspectionResponseRepository:
    def upsert(
        self,
        *,
        run: InspectionRun,
        checklist_item: InspectionChecklistItem,
        response: str,
        score: Decimal,
        comment: str,
        evidence_attachment_id: int | None,
        responded_by: User,
    ) -> InspectionStepResponse:
        obj = InspectionStepResponse.objects.filter(inspection_run=run, checklist_item=checklist_item).first()
        if obj:
            obj.response = response
            obj.score = score
            obj.comment = comment
            obj.evidence_attachment_id = evidence_attachment_id
            obj.responded_by = responded_by
            obj.responded_at = timezone.now()
            obj.save()
            return obj
        return InspectionStepResponse.objects.create(
            inspection_run=run,
            checklist_item=checklist_item,
            response=response,
            score=score,
            comment=comment,
            evidence_attachment_id=evidence_attachment_id,
            responded_by=responded_by,
            responded_at=timezone.now(),
        )


class InspectionHistoryRepository:
    def create(self, **kwargs) -> InspectionRunHistory:
        return InspectionRunHistory.objects.create(**kwargs)


class InspectionScoringService:
    ZERO = Decimal("0")
    ONE_HUNDRED = Decimal("100")

    def __init__(self, pass_threshold: Decimal = Decimal("90")) -> None:
        self.pass_threshold = pass_threshold

    def _safe_percent(self, numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator <= self.ZERO:
            return self.ZERO
        return ((numerator / denominator) * self.ONE_HUNDRED).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_response_score(self, *, item_weight: Decimal, response: str) -> Decimal:
        if response == InspectionStepResponse.RESPONSE_PASS:
            return item_weight
        return self.ZERO

    def calculate_run_score(self, *, run: InspectionRun) -> tuple[Decimal, str, dict]:
        items = list(
            InspectionChecklistItem.objects.filter(section__template_id=run.template_id)
            .select_related("section")
            .order_by("section__sort_order", "sort_order", "id")
        )
        responses = {
            row.checklist_item_id: row
            for row in InspectionStepResponse.objects.filter(inspection_run=run)
        }
        section_totals: dict[int, dict] = {}
        total_num = Decimal("0")
        total_den = Decimal("0")
        fail_count = 0
        applicable_count = 0

        for item in items:
            section_data = section_totals.setdefault(
                item.section_id,
                {
                    "section_id": item.section_id,
                    "title": item.section.title,
                    "applicable_weight": Decimal("0"),
                    "earned_weight": Decimal("0"),
                    "score": Decimal("0.00"),
                },
            )
            response = responses.get(item.id)
            if not response:
                continue
            if response.response == InspectionStepResponse.RESPONSE_NA:
                continue
            applicable_count += 1
            section_data["applicable_weight"] += item.weight
            total_den += item.weight
            if response.response == InspectionStepResponse.RESPONSE_FAIL:
                fail_count += 1
            earned = item.weight if response.response == InspectionStepResponse.RESPONSE_PASS else Decimal("0")
            section_data["earned_weight"] += earned
            total_num += earned

        for data in section_totals.values():
            data["score"] = self._safe_percent(data["earned_weight"], data["applicable_weight"])

        final_score = self._safe_percent(total_num, total_den)
        if applicable_count == 0:
            result = InspectionRun.RESULT_NOT_APPLICABLE
        elif final_score >= self.pass_threshold:
            result = InspectionRun.RESULT_PASS
        elif fail_count > 0:
            result = InspectionRun.RESULT_FAIL
        else:
            result = InspectionRun.RESULT_PARTIAL

        return final_score, result, {
            "sections": list(section_totals.values()),
            "applicable_items": applicable_count,
            "fail_count": fail_count,
        }


class InspectionValidationService:
    TERMINAL_STATUSES = {
        InspectionRun.STATUS_COMPLETED,
        InspectionRun.STATUS_CANCELLED,
        InspectionRun.STATUS_VOID,
    }

    def ensure_template_active(self, template: InspectionTemplate) -> None:
        if not template.is_active:
            raise InspectionValidationError("Inactive template cannot be used for inspection runs")

    def ensure_can_start(self, run: InspectionRun) -> None:
        if run.status in self.TERMINAL_STATUSES:
            raise InspectionValidationError("Cannot start completed/cancelled/void inspection")

    def ensure_can_respond(self, run: InspectionRun, *, admin_override: bool = False) -> None:
        if run.status == InspectionRun.STATUS_COMPLETED and admin_override:
            return
        if run.status in self.TERMINAL_STATUSES:
            raise InspectionValidationError("Cannot submit responses for terminal inspection")

    def ensure_can_complete(self, run: InspectionRun) -> None:
        if run.status in self.TERMINAL_STATUSES:
            raise InspectionValidationError("Cannot complete terminal inspection")
        if run.status != InspectionRun.STATUS_IN_PROGRESS:
            raise InspectionValidationError("Cannot complete inspection without starting it")

    def validate_response_payload(self, *, item: InspectionChecklistItem, response: str, comment: str, evidence_attachment_id: int | None) -> None:
        if item.response_type != InspectionChecklistItem.RESPONSE_TYPE_PASS_FAIL_NA:
            raise InspectionValidationError("Unsupported response type")
        if response not in {
            InspectionStepResponse.RESPONSE_PASS,
            InspectionStepResponse.RESPONSE_FAIL,
            InspectionStepResponse.RESPONSE_NA,
        }:
            raise InspectionValidationError("Invalid response")
        if response == InspectionStepResponse.RESPONSE_FAIL and not comment.strip():
            raise InspectionValidationError("Comment is required for FAIL response")
        if response == InspectionStepResponse.RESPONSE_FAIL and item.non_compliance_trigger and not evidence_attachment_id:
            raise InspectionValidationError("Evidence attachment is required for non-compliance FAIL")

    def validate_required_items_answered(self, *, run: InspectionRun) -> None:
        required_ids = set(
            InspectionChecklistItem.objects.filter(section__template_id=run.template_id, is_required=True).values_list("id", flat=True)
        )
        answered_ids = set(
            InspectionStepResponse.objects.filter(inspection_run=run).exclude(response="").values_list("checklist_item_id", flat=True)
        )
        missing = required_ids - answered_ids
        if missing:
            raise InspectionValidationError("Required checklist items must be answered before completion")


class NonComplianceAlertService:
    def __init__(self, *, publisher: InspectionEventPublisher | None = None) -> None:
        self.publisher = publisher or InspectionEventPublisher()

    def create_alert(
        self,
        *,
        run: InspectionRun,
        alert_type: str,
        message: str,
        checklist_item: InspectionChecklistItem | None = None,
        severity: str = NonComplianceAlert.SEVERITY_HIGH,
        assigned_to: User | None = None,
    ) -> NonComplianceAlert | None:
        exists = NonComplianceAlert.objects.filter(
            inspection_run=run,
            checklist_item=checklist_item,
            alert_type=alert_type,
            status__in=[NonComplianceAlert.STATUS_OPEN, NonComplianceAlert.STATUS_ACKNOWLEDGED],
        ).exists()
        if exists:
            return None
        created = NonComplianceAlert.objects.create(
            org_id=run.org_id,
            inspection_run=run,
            checklist_item=checklist_item,
            alert_type=alert_type,
            severity=severity,
            message=message,
            assigned_to=assigned_to,
            status=NonComplianceAlert.STATUS_OPEN,
        )
        try:
            self.publisher.publish_non_compliance_alert(alert=created)
        except Exception:
            pass
        return created

    def trigger_on_response(self, *, run: InspectionRun, item: InspectionChecklistItem, response: str, actor: User | None = None) -> list[NonComplianceAlert]:
        alerts: list[NonComplianceAlert] = []
        if response == InspectionStepResponse.RESPONSE_FAIL and item.non_compliance_trigger:
            created = self.create_alert(
                run=run,
                checklist_item=item,
                alert_type=NonComplianceAlert.ALERT_ITEM_FAIL,
                severity=NonComplianceAlert.SEVERITY_HIGH,
                message=f"Non-compliance on item: {item.question}",
                assigned_to=actor,
            )
            if created:
                alerts.append(created)
        return alerts

    def trigger_on_completion(self, *, run: InspectionRun, threshold: Decimal) -> list[NonComplianceAlert]:
        alerts: list[NonComplianceAlert] = []
        if run.result == InspectionRun.RESULT_FAIL:
            created = self.create_alert(
                run=run,
                checklist_item=None,
                alert_type=NonComplianceAlert.ALERT_FINAL_FAIL,
                severity=NonComplianceAlert.SEVERITY_CRITICAL,
                message="Inspection result is FAIL",
                assigned_to=run.assigned_to,
            )
            if created:
                alerts.append(created)
        if run.final_score < threshold:
            created = self.create_alert(
                run=run,
                checklist_item=None,
                alert_type=NonComplianceAlert.ALERT_SCORE_BELOW_THRESHOLD,
                severity=NonComplianceAlert.SEVERITY_HIGH,
                message=f"Inspection score {run.final_score} below threshold {threshold}",
                assigned_to=run.assigned_to,
            )
            if created:
                alerts.append(created)

        if run.asset_id:
            failures = InspectionRun.objects.filter(asset_id=run.asset_id, result=InspectionRun.RESULT_FAIL).count()
            if failures >= 2:
                created = self.create_alert(
                    run=run,
                    checklist_item=None,
                    alert_type=NonComplianceAlert.ALERT_REPEAT_FAILURE,
                    severity=NonComplianceAlert.SEVERITY_CRITICAL,
                    message=f"Repeated failures detected for asset {run.asset_id}",
                    assigned_to=run.assigned_to,
                )
                if created:
                    alerts.append(created)
        return alerts


class InspectionExecutionService:
    def __init__(
        self,
        *,
        template_repository: InspectionTemplateRepository | None = None,
        run_repository: InspectionRunRepository | None = None,
        response_repository: InspectionResponseRepository | None = None,
        history_repository: InspectionHistoryRepository | None = None,
        scoring_service: InspectionScoringService | None = None,
        validation_service: InspectionValidationService | None = None,
        alert_service: NonComplianceAlertService | None = None,
        event_publisher: InspectionEventPublisher | None = None,
    ) -> None:
        self.template_repository = template_repository or InspectionTemplateRepository()
        self.run_repository = run_repository or InspectionRunRepository()
        self.response_repository = response_repository or InspectionResponseRepository()
        self.history_repository = history_repository or InspectionHistoryRepository()
        self.scoring_service = scoring_service or InspectionScoringService()
        self.validation_service = validation_service or InspectionValidationService()
        self.event_publisher = event_publisher or InspectionEventPublisher()
        self.alert_service = alert_service or NonComplianceAlertService(publisher=self.event_publisher)

    def _inspection_number(self, run_id: int) -> str:
        return f"INSP-{run_id:08d}"

    @transaction.atomic
    def create_run(self, *, org_id: int, template: InspectionTemplate, created_by: User, **payload) -> InspectionRun:
        self.validation_service.ensure_template_active(template)
        run = self.run_repository.create(
            org_id=org_id,
            inspection_number=f"TMP-{timezone.now().timestamp()}",
            template=template,
            property_id=payload.get("property_id") or template.property_id,
            department_id=payload.get("department_id") or template.department_id,
            location_id=payload.get("location_id"),
            room_id=payload.get("room_id"),
            asset_id=payload.get("asset_id"),
            assigned_to=payload.get("assigned_to"),
            inspected_by=payload.get("inspected_by"),
            status=InspectionRun.STATUS_SCHEDULED,
            result=InspectionRun.RESULT_PARTIAL,
            final_score=Decimal("0.00"),
            notes=payload.get("notes", ""),
            created_by=created_by,
        )
        run.inspection_number = self._inspection_number(run.id)
        run.save(update_fields=["inspection_number", "updated_at"])
        self.history_repository.create(
            inspection_run=run,
            action="inspection_run_created",
            actor=created_by,
            metadata_json={},
        )
        return run

    @transaction.atomic
    def start_run(self, *, run: InspectionRun, actor: User) -> InspectionRun:
        self.validation_service.ensure_can_start(run)
        if run.status == InspectionRun.STATUS_IN_PROGRESS:
            return run
        run.status = InspectionRun.STATUS_IN_PROGRESS
        if not run.started_at:
            run.started_at = timezone.now()
        run.inspected_by = run.inspected_by or actor
        run.save(update_fields=["status", "started_at", "inspected_by", "updated_at"])
        self.history_repository.create(inspection_run=run, action="inspection_run_started", actor=actor, metadata_json={})
        return run

    @transaction.atomic
    def submit_response(
        self,
        *,
        run: InspectionRun,
        checklist_item: InspectionChecklistItem,
        response: str,
        comment: str,
        evidence_attachment_id: int | None,
        actor: User,
        admin_override: bool = False,
    ) -> tuple[InspectionStepResponse, Decimal, str, list[NonComplianceAlert]]:
        self.validation_service.ensure_can_respond(run, admin_override=admin_override)
        self.validation_service.validate_response_payload(
            item=checklist_item,
            response=response,
            comment=comment,
            evidence_attachment_id=evidence_attachment_id,
        )
        score = self.scoring_service.calculate_response_score(item_weight=checklist_item.weight, response=response)
        row = self.response_repository.upsert(
            run=run,
            checklist_item=checklist_item,
            response=response,
            score=score,
            comment=comment,
            evidence_attachment_id=evidence_attachment_id,
            responded_by=actor,
        )
        final_score, result, _ = self.scoring_service.calculate_run_score(run=run)
        run.final_score = final_score
        run.result = result
        updates = ["final_score", "result", "updated_at"]
        if run.status == InspectionRun.STATUS_COMPLETED and admin_override:
            run.status = InspectionRun.STATUS_IN_PROGRESS
            run.completed_at = None
            updates.extend(["status", "completed_at"])
        run.save(update_fields=updates)
        alerts = self.alert_service.trigger_on_response(run=run, item=checklist_item, response=response, actor=actor)
        self.history_repository.create(
            inspection_run=run,
            action="inspection_response_submitted",
            actor=actor,
            metadata_json={"item_id": checklist_item.id, "response": response},
        )
        return row, final_score, result, alerts

    @transaction.atomic
    def complete_run(self, *, run: InspectionRun, actor: User) -> tuple[InspectionRun, list[NonComplianceAlert]]:
        self.validation_service.ensure_can_complete(run)
        self.validation_service.validate_required_items_answered(run=run)
        final_score, result, _ = self.scoring_service.calculate_run_score(run=run)
        run.final_score = final_score
        run.result = result
        run.status = InspectionRun.STATUS_COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=["final_score", "result", "status", "completed_at", "updated_at"])
        alerts = self.alert_service.trigger_on_completion(run=run, threshold=self.scoring_service.pass_threshold)
        try:
            self.event_publisher.publish_inspection_completed(run=run)
        except Exception:
            pass
        self.history_repository.create(
            inspection_run=run,
            action="inspection_run_completed",
            actor=actor,
            metadata_json={"final_score": str(final_score), "result": result},
        )
        return run, alerts


class InspectionReportingService:
    def summary(self, *, org_id: int, date_from: datetime | None = None, date_to: datetime | None = None, **filters):
        qs = InspectionRun.objects.filter(org_id=org_id)
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)
        for field in ["property_id", "department_id", "location_id", "room_id", "asset_id", "inspected_by_id", "template_id"]:
            value = filters.get(field)
            if value:
                qs = qs.filter(**{field: value})

        aggregate = qs.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=InspectionRun.STATUS_COMPLETED)),
            passed=Count("id", filter=Q(result=InspectionRun.RESULT_PASS)),
            failed=Count("id", filter=Q(result=InspectionRun.RESULT_FAIL)),
            avg_score=Avg("final_score"),
        )
        non_compliance_count = NonComplianceAlert.objects.filter(org_id=org_id).count()
        by_result = dict(qs.values_list("result").annotate(count=Count("id")))
        by_category = dict(qs.values_list("template__category").annotate(count=Count("id")))
        return {
            "total_inspections": aggregate["total"] or 0,
            "completed_inspections": aggregate["completed"] or 0,
            "passed_inspections": aggregate["passed"] or 0,
            "failed_inspections": aggregate["failed"] or 0,
            "average_score": float((aggregate["avg_score"] or Decimal("0")).quantize(Decimal("0.01"))),
            "non_compliance_count": non_compliance_count,
            "inspections_by_result": by_result,
            "inspections_by_category": by_category,
        }

    def trends(self, *, org_id: int, group_by: str = "day", **filters):
        trunc = TruncDay("created_at")
        if group_by == "week":
            trunc = TruncWeek("created_at")
        elif group_by == "month":
            trunc = TruncMonth("created_at")
        qs = InspectionRun.objects.filter(org_id=org_id)
        if filters.get("date_from"):
            qs = qs.filter(created_at__gte=filters["date_from"])
        if filters.get("date_to"):
            qs = qs.filter(created_at__lte=filters["date_to"])
        rows = (
            qs.annotate(period=trunc)
            .values("period")
            .annotate(total=Count("id"), average_score=Avg("final_score"), failed=Count("id", filter=Q(result=InspectionRun.RESULT_FAIL)))
            .order_by("period")
        )
        return [
            {
                "period": row["period"],
                "total_inspections": row["total"],
                "average_score": float((row["average_score"] or Decimal("0")).quantize(Decimal("0.01"))),
                "failed_inspections": row["failed"],
            }
            for row in rows
        ]

    def non_compliance(self, *, org_id: int, **filters):
        qs = NonComplianceAlert.objects.filter(org_id=org_id)
        if filters.get("date_from"):
            qs = qs.filter(created_at__gte=filters["date_from"])
        if filters.get("date_to"):
            qs = qs.filter(created_at__lte=filters["date_to"])
        return {
            "count": qs.count(),
            "results": [
                {
                    "id": row.id,
                    "inspection_run_id": row.inspection_run_id,
                    "checklist_item_id": row.checklist_item_id,
                    "alert_type": row.alert_type,
                    "severity": row.severity,
                    "message": row.message,
                    "assigned_to": row.assigned_to_id,
                    "status": row.status,
                    "created_at": row.created_at,
                    "resolved_at": row.resolved_at,
                }
                for row in qs.order_by("-created_at")
            ],
        }
