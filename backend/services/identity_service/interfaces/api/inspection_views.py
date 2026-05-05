from django.db.models import Q
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.services.audit_logging import AuditContext
from application.services.inspections import (
    InspectionExecutionService,
    InspectionNotFoundError,
    InspectionReportingService,
    InspectionRunFilters,
    InspectionTemplateRepository,
    InspectionValidationError,
)
from infrastructure.db.core.models import (
    InspectionChecklistItem,
    InspectionChecklistSection,
    InspectionRun,
    InspectionTemplate,
    NonComplianceAlert,
    RolePermission,
    User,
    UserRole,
)
from infrastructure.services.audit_logging import get_audit_logger
from interfaces.api.serializers import (
    InspectionAlertActionSerializer,
    InspectionResponseSubmitSerializer,
    InspectionRunCreateSerializer,
    InspectionRunUpdateResponseSerializer,
    InspectionTemplateCreateSerializer,
    InspectionTemplateUpdateSerializer,
)


def _has_permission(user, code: str) -> bool:
    if not user:
        return False
    if hasattr(user, "is_authenticated") and not user.is_authenticated:
        return False
    if UserRole.objects.filter(user=user, role__name__iexact="super admin").exists():
        return True
    return RolePermission.objects.filter(role__user_roles__user=user, permission__code=code).exists()


def _audit_context(request, *, org_id: int, property_id=None, actor=None):
    meta = getattr(request, "audit_context", {})
    return AuditContext(
        org_id=org_id,
        property_id=property_id,
        actor_user_id=getattr(actor, "id", None),
        ip_address=meta.get("ip_address", request.META.get("REMOTE_ADDR", "")),
        user_agent=meta.get("user_agent", request.META.get("HTTP_USER_AGENT", "")),
    )


def _audit(request, *, org_id: int, action: str, entity_type: str, entity_id: str, metadata=None, property_id=None, actor=None):
    try:
        get_audit_logger().log_action(
            action=action,
            target_type=entity_type,
            target_id=str(entity_id),
            metadata=metadata or {},
            context=_audit_context(request, org_id=org_id, property_id=property_id, actor=actor),
        )
    except Exception:
        pass


def _template_dict(template: InspectionTemplate) -> dict:
    sections = InspectionChecklistSection.objects.filter(template=template).order_by("sort_order", "id")
    payload_sections = []
    for section in sections:
        items = InspectionChecklistItem.objects.filter(section=section).order_by("sort_order", "id")
        payload_sections.append(
            {
                "id": section.id,
                "title": section.title,
                "description": section.description,
                "sort_order": section.sort_order,
                "weight": section.weight,
                "items": [
                    {
                        "id": item.id,
                        "question": item.question,
                        "description": item.description,
                        "response_type": item.response_type,
                        "is_required": item.is_required,
                        "weight": item.weight,
                        "sort_order": item.sort_order,
                        "non_compliance_trigger": item.non_compliance_trigger,
                    }
                    for item in items
                ],
            }
        )
    return {
        "id": template.id,
        "template_code": template.template_code,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "property_id": template.property_id,
        "department_id": template.department_id,
        "is_active": template.is_active,
        "version": template.version,
        "sections": payload_sections,
        "created_by": template.created_by_id,
        "updated_by": template.updated_by_id,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }


def _run_dict(run: InspectionRun) -> dict:
    return {
        "id": run.id,
        "inspection_number": run.inspection_number,
        "template_id": run.template_id,
        "property_id": run.property_id,
        "department_id": run.department_id,
        "location_id": run.location_id,
        "room_id": run.room_id,
        "asset_id": run.asset_id,
        "assigned_to": run.assigned_to_id,
        "inspected_by": run.inspected_by_id,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "final_score": run.final_score,
        "result": run.result,
        "notes": run.notes,
        "created_by": run.created_by_id,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }


class InspectionTemplateListCreateView(APIView):
    template_repository = InspectionTemplateRepository()

    @extend_schema(request=InspectionTemplateCreateSerializer)
    def post(self, request):
        if not _has_permission(request.user, "inspections.templates.manage"):
            return Response({"detail": "Permission required: inspections.templates.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = InspectionTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if InspectionTemplate.objects.filter(template_code=data["template_code"]).exists():
            return Response({"detail": "template_code must be unique"}, status=status.HTTP_409_CONFLICT)
        template = InspectionTemplate.objects.create(
            org_id=data["org_id"],
            template_code=data["template_code"],
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", ""),
            property_id=data.get("property_id"),
            department_id=data.get("department_id"),
            is_active=data.get("is_active", True),
            version=data.get("version", 1),
            created_by=request.user,
            updated_by=request.user,
        )
        for section_payload in data.get("sections", []):
            section = InspectionChecklistSection.objects.create(
                template=template,
                title=section_payload["title"],
                description=section_payload.get("description", ""),
                sort_order=section_payload.get("sort_order", 0),
                weight=section_payload.get("weight", "0"),
            )
            for item_payload in section_payload.get("items", []):
                InspectionChecklistItem.objects.create(
                    section=section,
                    question=item_payload["question"],
                    description=item_payload.get("description", ""),
                    response_type=item_payload.get("response_type", "PASS_FAIL_NA"),
                    is_required=item_payload.get("is_required", False),
                    weight=item_payload.get("weight", "0"),
                    sort_order=item_payload.get("sort_order", 0),
                    non_compliance_trigger=item_payload.get("non_compliance_trigger", False),
                )
        _audit(request, org_id=template.org_id, action="inspection_template_created", entity_type="inspection_template", entity_id=str(template.id), metadata={"template_code": template.template_code}, property_id=template.property_id, actor=request.user)
        return Response(_template_dict(template), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "inspections.templates.view"):
            return Response({"detail": "Permission required: inspections.templates.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        is_active = request.query_params.get("is_active")
        templates = InspectionTemplate.objects.filter(org_id=org_id)
        if is_active is not None:
            templates = templates.filter(is_active=is_active.lower() == "true")
        q = request.query_params.get("q", "").strip()
        if q:
            templates = templates.filter(Q(name__icontains=q) | Q(template_code__icontains=q) | Q(category__icontains=q))
        rows = templates.order_by("-updated_at")
        return Response({"count": rows.count(), "results": [_template_dict(row) for row in rows]})


class InspectionTemplateDetailView(APIView):
    def get(self, request, template_id: int):
        if not _has_permission(request.user, "inspections.templates.view"):
            return Response({"detail": "Permission required: inspections.templates.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        template = InspectionTemplate.objects.filter(id=template_id, org_id=org_id).first()
        if not template:
            return Response({"detail": "Inspection template not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_template_dict(template), status=status.HTTP_200_OK)

    def patch(self, request, template_id: int):
        if not _has_permission(request.user, "inspections.templates.manage"):
            return Response({"detail": "Permission required: inspections.templates.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = InspectionTemplateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        org_id = int(request.data.get("org_id", 0))
        template = InspectionTemplate.objects.filter(id=template_id, org_id=org_id).first()
        if not template:
            return Response({"detail": "Inspection template not found"}, status=status.HTTP_404_NOT_FOUND)
        for key in ["name", "description", "category", "property_id", "department_id", "is_active", "version"]:
            if key in serializer.validated_data:
                setattr(template, key, serializer.validated_data[key])
        template.updated_by = request.user
        with transaction.atomic():
            template.save()
            if "sections" in serializer.validated_data:
                section_payloads = serializer.validated_data["sections"]
                existing_sections = {section.id: section for section in InspectionChecklistSection.objects.filter(template=template)}
                payload_section_ids = set()

                for section_payload in section_payloads:
                    section_id = section_payload.get("id")
                    if section_id and section_id in existing_sections:
                        section = existing_sections[section_id]
                        section.title = section_payload["title"]
                        section.description = section_payload.get("description", "")
                        section.sort_order = section_payload.get("sort_order", section.sort_order)
                        section.weight = section_payload.get("weight", section.weight)
                        section.save()
                    else:
                        section = InspectionChecklistSection.objects.create(
                            template=template,
                            title=section_payload["title"],
                            description=section_payload.get("description", ""),
                            sort_order=section_payload.get("sort_order", 0),
                            weight=section_payload.get("weight", "0"),
                        )
                    payload_section_ids.add(section.id)

                    existing_items = {item.id: item for item in InspectionChecklistItem.objects.filter(section=section)}
                    payload_item_ids = set()
                    for item_payload in section_payload.get("items", []):
                        item_id = item_payload.get("id")
                        if item_id and item_id in existing_items:
                            item = existing_items[item_id]
                            item.question = item_payload["question"]
                            item.description = item_payload.get("description", "")
                            item.response_type = item_payload.get("response_type", "PASS_FAIL_NA")
                            item.is_required = item_payload.get("is_required", False)
                            item.weight = item_payload.get("weight", "0")
                            item.sort_order = item_payload.get("sort_order", 0)
                            item.non_compliance_trigger = item_payload.get("non_compliance_trigger", False)
                            item.save()
                        else:
                            item = InspectionChecklistItem.objects.create(
                                section=section,
                                question=item_payload["question"],
                                description=item_payload.get("description", ""),
                                response_type=item_payload.get("response_type", "PASS_FAIL_NA"),
                                is_required=item_payload.get("is_required", False),
                                weight=item_payload.get("weight", "0"),
                                sort_order=item_payload.get("sort_order", 0),
                                non_compliance_trigger=item_payload.get("non_compliance_trigger", False),
                            )
                        payload_item_ids.add(item.id)

                    for existing_item_id, existing_item in existing_items.items():
                        if existing_item_id not in payload_item_ids:
                            existing_item.delete()

                for existing_section_id, existing_section in existing_sections.items():
                    if existing_section_id not in payload_section_ids:
                        existing_section.delete()
        _audit(request, org_id=template.org_id, action="inspection_template_updated", entity_type="inspection_template", entity_id=str(template.id), metadata={}, property_id=template.property_id, actor=request.user)
        return Response(_template_dict(template), status=status.HTTP_200_OK)


class InspectionTemplateActivationView(APIView):
    active_value = True
    action_name = "inspection_template_activated"

    def post(self, request, template_id: int):
        if not _has_permission(request.user, "inspections.templates.manage"):
            return Response({"detail": "Permission required: inspections.templates.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        template = InspectionTemplate.objects.filter(id=template_id, org_id=org_id).first()
        if not template:
            return Response({"detail": "Inspection template not found"}, status=status.HTTP_404_NOT_FOUND)
        template.is_active = self.active_value
        template.updated_by = request.user
        template.save(update_fields=["is_active", "updated_by", "updated_at"])
        _audit(request, org_id=template.org_id, action=self.action_name, entity_type="inspection_template", entity_id=str(template.id), metadata={"is_active": template.is_active}, property_id=template.property_id, actor=request.user)
        return Response(_template_dict(template), status=status.HTTP_200_OK)


class InspectionTemplateDeactivateView(InspectionTemplateActivationView):
    active_value = False
    action_name = "inspection_template_deactivated"


class InspectionRunListCreateView(APIView):
    service = InspectionExecutionService()

    def post(self, request):
        if not _has_permission(request.user, "inspections.runs.manage"):
            return Response({"detail": "Permission required: inspections.runs.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = InspectionRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        template = InspectionTemplate.objects.filter(id=data["template_id"], org_id=data["org_id"]).first()
        if not template:
            return Response({"detail": "Inspection template not found"}, status=status.HTTP_404_NOT_FOUND)
        assigned_to = User.objects.filter(id=data.get("assigned_to"), org_id=data["org_id"]).first() if data.get("assigned_to") else None
        inspected_by = User.objects.filter(id=data.get("inspected_by"), org_id=data["org_id"]).first() if data.get("inspected_by") else None
        try:
            run = self.service.create_run(
                org_id=data["org_id"],
                template=template,
                created_by=request.user,
                property_id=data.get("property_id"),
                department_id=data.get("department_id"),
                location_id=data.get("location_id"),
                room_id=data.get("room_id"),
                asset_id=data.get("asset_id"),
                assigned_to=assigned_to,
                inspected_by=inspected_by,
                notes=data.get("notes", ""),
            )
        except InspectionValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=run.org_id, action="inspection_run_created", entity_type="inspection_run", entity_id=str(run.id), metadata={"inspection_number": run.inspection_number}, property_id=run.property_id, actor=request.user)
        return Response(_run_dict(run), status=status.HTTP_201_CREATED)

    def get(self, request):
        if not _has_permission(request.user, "inspections.runs.view"):
            return Response({"detail": "Permission required: inspections.runs.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        filters = InspectionRunFilters(
            org_id=org_id,
            template_id=int(request.query_params["template_id"]) if request.query_params.get("template_id") else None,
            status=request.query_params.get("status"),
            result=request.query_params.get("result"),
            property_id=int(request.query_params["property"]) if request.query_params.get("property") else None,
            department_id=int(request.query_params["department"]) if request.query_params.get("department") else None,
            location_id=int(request.query_params["location"]) if request.query_params.get("location") else None,
            room_id=int(request.query_params["room"]) if request.query_params.get("room") else None,
            asset_id=int(request.query_params["asset"]) if request.query_params.get("asset") else None,
            assigned_to=int(request.query_params["assigned_to"]) if request.query_params.get("assigned_to") else None,
            inspected_by=int(request.query_params["inspected_by"]) if request.query_params.get("inspected_by") else None,
        )
        qs = self.service.run_repository.list(filters).order_by("-created_at")
        return Response({"count": qs.count(), "results": [_run_dict(row) for row in qs]})


class InspectionRunDetailView(APIView):
    service = InspectionExecutionService()

    def get(self, request, run_id: int):
        if not _has_permission(request.user, "inspections.runs.view"):
            return Response({"detail": "Permission required: inspections.runs.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        try:
            run = self.service.run_repository.get_for_org(org_id=org_id, run_id=run_id)
        except InspectionNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_run_dict(run), status=status.HTTP_200_OK)


class InspectionRunStartView(APIView):
    service = InspectionExecutionService()

    def post(self, request, run_id: int):
        if not _has_permission(request.user, "inspections.runs.manage"):
            return Response({"detail": "Permission required: inspections.runs.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        try:
            run = self.service.run_repository.get_for_org(org_id=org_id, run_id=run_id)
            run = self.service.start_run(run=run, actor=request.user)
        except (InspectionNotFoundError, InspectionValidationError) as exc:
            code = status.HTTP_404_NOT_FOUND if isinstance(exc, InspectionNotFoundError) else status.HTTP_400_BAD_REQUEST
            return Response({"detail": str(exc)}, status=code)
        _audit(request, org_id=run.org_id, action="inspection_run_started", entity_type="inspection_run", entity_id=str(run.id), metadata={}, property_id=run.property_id, actor=request.user)
        return Response(_run_dict(run), status=status.HTTP_200_OK)


class InspectionRunResponseView(APIView):
    service = InspectionExecutionService()

    def post(self, request, run_id: int):
        if not _has_permission(request.user, "inspections.runs.manage"):
            return Response({"detail": "Permission required: inspections.runs.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = InspectionResponseSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        admin_override = data.get("admin_override", False)
        if admin_override and not _has_permission(request.user, "inspections.runs.admin_override"):
            return Response({"detail": "Permission required: inspections.runs.admin_override"}, status=status.HTTP_403_FORBIDDEN)
        try:
            run = self.service.run_repository.get_for_org(org_id=data["org_id"], run_id=run_id)
        except InspectionNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        item = InspectionChecklistItem.objects.filter(id=data["checklist_item_id"], section__template_id=run.template_id).first()
        if not item:
            return Response({"detail": "Checklist item not found in template"}, status=status.HTTP_404_NOT_FOUND)
        try:
            row, final_score, result, alerts = self.service.submit_response(
                run=run,
                checklist_item=item,
                response=data["response"],
                comment=data.get("comment", ""),
                evidence_attachment_id=data.get("evidence_attachment_id"),
                actor=request.user,
                admin_override=admin_override,
            )
        except InspectionValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=run.org_id, action="inspection_response_submitted", entity_type="inspection_run", entity_id=str(run.id), metadata={"response_id": row.id}, property_id=run.property_id, actor=request.user)
        for alert in alerts:
            _audit(request, org_id=run.org_id, action="non_compliance_alert_created", entity_type="non_compliance_alert", entity_id=str(alert.id), metadata={"alert_type": alert.alert_type}, property_id=run.property_id, actor=request.user)
        return Response({
            "response": {
                "id": row.id,
                "inspection_run_id": row.inspection_run_id,
                "checklist_item_id": row.checklist_item_id,
                "response": row.response,
                "score": row.score,
                "comment": row.comment,
                "evidence_attachment_id": row.evidence_attachment_id,
                "responded_by": row.responded_by_id,
                "responded_at": row.responded_at,
            },
            "run_score": final_score,
            "run_result": result,
            "alerts_created": [a.id for a in alerts],
        }, status=status.HTTP_201_CREATED)


class InspectionRunResponseDetailView(APIView):
    service = InspectionExecutionService()

    def patch(self, request, run_id: int, response_id: int):
        if not _has_permission(request.user, "inspections.runs.manage"):
            return Response({"detail": "Permission required: inspections.runs.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = InspectionRunUpdateResponseSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        admin_override = data.get("admin_override", False)
        if admin_override and not _has_permission(request.user, "inspections.runs.admin_override"):
            return Response({"detail": "Permission required: inspections.runs.admin_override"}, status=status.HTTP_403_FORBIDDEN)
        run = InspectionRun.objects.filter(id=run_id, org_id=data["org_id"]).first()
        if not run:
            return Response({"detail": "Inspection run not found"}, status=status.HTTP_404_NOT_FOUND)
        response_obj = run.responses.filter(id=response_id).first()
        if not response_obj:
            return Response({"detail": "Inspection response not found"}, status=status.HTTP_404_NOT_FOUND)
        payload = {
            "org_id": data["org_id"],
            "checklist_item_id": response_obj.checklist_item_id,
            "response": data.get("response", response_obj.response),
            "comment": data.get("comment", response_obj.comment),
            "evidence_attachment_id": data.get("evidence_attachment_id", response_obj.evidence_attachment_id),
        }
        submit_serializer = InspectionResponseSubmitSerializer(data=payload)
        submit_serializer.is_valid(raise_exception=True)
        item = response_obj.checklist_item
        try:
            row, final_score, result, alerts = self.service.submit_response(
                run=run,
                checklist_item=item,
                response=payload["response"],
                comment=payload.get("comment", ""),
                evidence_attachment_id=payload.get("evidence_attachment_id"),
                actor=request.user,
                admin_override=admin_override,
            )
        except InspectionValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        _audit(request, org_id=run.org_id, action="inspection_response_updated", entity_type="inspection_run", entity_id=str(run.id), metadata={"response_id": row.id}, property_id=run.property_id, actor=request.user)
        return Response({"response_id": row.id, "run_score": final_score, "run_result": result, "alerts_created": [a.id for a in alerts]}, status=status.HTTP_200_OK)


class InspectionRunCompleteView(APIView):
    service = InspectionExecutionService()

    def post(self, request, run_id: int):
        if not _has_permission(request.user, "inspections.runs.manage"):
            return Response({"detail": "Permission required: inspections.runs.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        try:
            run = self.service.run_repository.get_for_org(org_id=org_id, run_id=run_id)
            run, alerts = self.service.complete_run(run=run, actor=request.user)
        except (InspectionNotFoundError, InspectionValidationError) as exc:
            code = status.HTTP_404_NOT_FOUND if isinstance(exc, InspectionNotFoundError) else status.HTTP_400_BAD_REQUEST
            return Response({"detail": str(exc)}, status=code)
        _audit(request, org_id=run.org_id, action="inspection_score_calculated", entity_type="inspection_run", entity_id=str(run.id), metadata={"score": str(run.final_score), "result": run.result}, property_id=run.property_id, actor=request.user)
        _audit(request, org_id=run.org_id, action="inspection_run_completed", entity_type="inspection_run", entity_id=str(run.id), metadata={"score": str(run.final_score), "result": run.result}, property_id=run.property_id, actor=request.user)
        for alert in alerts:
            _audit(request, org_id=run.org_id, action="non_compliance_alert_created", entity_type="non_compliance_alert", entity_id=str(alert.id), metadata={"alert_type": alert.alert_type}, property_id=run.property_id, actor=request.user)
        return Response({**_run_dict(run), "alerts_created": [a.id for a in alerts]}, status=status.HTTP_200_OK)


class InspectionRunCancelView(APIView):
    to_status = InspectionRun.STATUS_CANCELLED
    action = "inspection_run_cancelled"

    def post(self, request, run_id: int):
        if not _has_permission(request.user, "inspections.runs.manage"):
            return Response({"detail": "Permission required: inspections.runs.manage"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.data.get("org_id", 0))
        run = InspectionRun.objects.filter(id=run_id, org_id=org_id).first()
        if not run:
            return Response({"detail": "Inspection run not found"}, status=status.HTTP_404_NOT_FOUND)
        if run.status in [InspectionRun.STATUS_COMPLETED, InspectionRun.STATUS_CANCELLED, InspectionRun.STATUS_VOID]:
            return Response({"detail": "Inspection run is terminal"}, status=status.HTTP_400_BAD_REQUEST)
        run.status = self.to_status
        run.save(update_fields=["status", "updated_at"])
        _audit(request, org_id=run.org_id, action=self.action, entity_type="inspection_run", entity_id=str(run.id), metadata={}, property_id=run.property_id, actor=request.user)
        return Response(_run_dict(run), status=status.HTTP_200_OK)


class InspectionRunVoidView(InspectionRunCancelView):
    to_status = InspectionRun.STATUS_VOID
    action = "inspection_run_voided"


class InspectionSummaryReportView(APIView):
    service = InspectionReportingService()

    def get(self, request):
        if not _has_permission(request.user, "inspections.reports.view"):
            return Response({"detail": "Permission required: inspections.reports.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        payload = self.service.summary(org_id=org_id)
        _audit(request, org_id=org_id, action="inspection_report_viewed", entity_type="inspection_report", entity_id="summary", metadata={}, actor=request.user)
        return Response(payload)


class InspectionTrendReportView(APIView):
    service = InspectionReportingService()

    def get(self, request):
        if not _has_permission(request.user, "inspections.reports.view"):
            return Response({"detail": "Permission required: inspections.reports.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        group_by = request.query_params.get("group_by", "day")
        payload = self.service.trends(org_id=org_id, group_by=group_by)
        _audit(request, org_id=org_id, action="inspection_report_viewed", entity_type="inspection_report", entity_id="trends", metadata={"group_by": group_by}, actor=request.user)
        return Response({"results": payload})


class InspectionNonComplianceReportView(APIView):
    service = InspectionReportingService()

    def get(self, request):
        if not _has_permission(request.user, "inspections.reports.view"):
            return Response({"detail": "Permission required: inspections.reports.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        payload = self.service.non_compliance(org_id=org_id)
        _audit(request, org_id=org_id, action="inspection_report_viewed", entity_type="inspection_report", entity_id="non_compliance", metadata={}, actor=request.user)
        return Response(payload)


class InspectionRunHistoryView(APIView):
    def get(self, request, run_id: int):
        if not _has_permission(request.user, "inspections.runs.view"):
            return Response({"detail": "Permission required: inspections.runs.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        run = InspectionRun.objects.filter(id=run_id, org_id=org_id).first()
        if not run:
            return Response({"detail": "Inspection run not found"}, status=status.HTTP_404_NOT_FOUND)
        rows = run.history.order_by("created_at")
        return Response(
            {
                "count": rows.count(),
                "results": [
                    {
                        "id": row.id,
                        "action": row.action,
                        "actor_id": row.actor_id,
                        "metadata": row.metadata_json,
                        "created_at": row.created_at,
                    }
                    for row in rows
                ],
            }
        )


class NonComplianceAlertListView(APIView):
    def get(self, request):
        if not _has_permission(request.user, "inspections.alerts.view"):
            return Response({"detail": "Permission required: inspections.alerts.view"}, status=status.HTTP_403_FORBIDDEN)
        org_id = int(request.query_params.get("org_id", "0"))
        if not org_id:
            return Response({"detail": "org_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        rows = NonComplianceAlert.objects.filter(org_id=org_id).order_by("-created_at")
        return Response(
            {
                "count": rows.count(),
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
                    for row in rows
                ],
            }
        )


class NonComplianceAlertActionView(APIView):
    new_status = NonComplianceAlert.STATUS_ACKNOWLEDGED
    action = "non_compliance_alert_acknowledged"

    def post(self, request, alert_id: int):
        if not _has_permission(request.user, "inspections.alerts.manage"):
            return Response({"detail": "Permission required: inspections.alerts.manage"}, status=status.HTTP_403_FORBIDDEN)
        serializer = InspectionAlertActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_id = serializer.validated_data["org_id"]
        row = NonComplianceAlert.objects.filter(id=alert_id, org_id=org_id).first()
        if not row:
            return Response({"detail": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
        row.status = self.new_status
        if self.new_status == NonComplianceAlert.STATUS_RESOLVED:
            from django.utils import timezone

            row.resolved_at = timezone.now()
            row.save(update_fields=["status", "resolved_at"])
        else:
            row.save(update_fields=["status"])
        _audit(request, org_id=row.org_id, action=self.action, entity_type="non_compliance_alert", entity_id=str(row.id), metadata={}, property_id=row.inspection_run.property_id if row.inspection_run else None, actor=request.user)
        return Response({"id": row.id, "status": row.status, "resolved_at": row.resolved_at}, status=status.HTTP_200_OK)


class NonComplianceAlertResolveView(NonComplianceAlertActionView):
    new_status = NonComplianceAlert.STATUS_RESOLVED
    action = "non_compliance_alert_resolved"
