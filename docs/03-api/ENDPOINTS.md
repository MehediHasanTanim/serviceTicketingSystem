# API Endpoints (High-Level)

This document lists planned REST API endpoints by domain. These are placeholders for design and alignment; detailed request/response schemas will be added per service.

## Identity & Access Service
- POST /api/v1/orgs
- GET /api/v1/orgs
- GET /api/v1/orgs/{orgId}
- PATCH /api/v1/orgs/{orgId}

- POST /api/v1/properties
- GET /api/v1/properties
- GET /api/v1/properties/{propertyId}
- PATCH /api/v1/properties/{propertyId}

- POST /api/v1/departments
- GET /api/v1/departments
- GET /api/v1/departments/{departmentId}
- PATCH /api/v1/departments/{departmentId}

- POST /api/v1/users
- GET /api/v1/users
- GET /api/v1/users/{userId}
- PATCH /api/v1/users/{userId}
- POST /api/v1/users/{userId}/invite
- POST /api/v1/users/{userId}/suspend
- POST /api/v1/users/{userId}/reactivate

- POST /api/v1/roles
- GET /api/v1/roles
- GET /api/v1/roles/{roleId}
- PATCH /api/v1/roles/{roleId}

- POST /api/v1/permissions
- GET /api/v1/permissions
- GET /api/v1/permissions/{permissionId}

- POST /api/v1/roles/{roleId}/permissions
- DELETE /api/v1/roles/{roleId}/permissions/{permissionId}

- POST /api/v1/users/{userId}/roles
- DELETE /api/v1/users/{userId}/roles/{roleId}

- POST /api/v1/users/{userId}/departments
- DELETE /api/v1/users/{userId}/departments/{departmentId}
- POST /api/v1/users/{userId}/departments/{departmentId}/primary

## Property Structure
- POST /api/v1/buildings
- GET /api/v1/buildings
- GET /api/v1/buildings/{buildingId}
- PATCH /api/v1/buildings/{buildingId}

- POST /api/v1/floors
- GET /api/v1/floors
- GET /api/v1/floors/{floorId}
- PATCH /api/v1/floors/{floorId}

- POST /api/v1/zones
- GET /api/v1/zones
- GET /api/v1/zones/{zoneId}
- PATCH /api/v1/zones/{zoneId}

- POST /api/v1/rooms
- GET /api/v1/rooms
- GET /api/v1/rooms/{roomId}
- PATCH /api/v1/rooms/{roomId}

## Work Orders Service
- POST /api/v1/work-orders
- GET /api/v1/work-orders
- GET /api/v1/work-orders/{workOrderId}
- PATCH /api/v1/work-orders/{workOrderId}
- POST /api/v1/work-orders/{workOrderId}/assign
- POST /api/v1/work-orders/{workOrderId}/start
- POST /api/v1/work-orders/{workOrderId}/stop
- POST /api/v1/work-orders/{workOrderId}/defer
- POST /api/v1/work-orders/{workOrderId}/complete
- POST /api/v1/work-orders/{workOrderId}/void
- POST /api/v1/work-orders/{workOrderId}/remarks
- POST /api/v1/work-orders/{workOrderId}/attachments
- POST /api/v1/work-orders/{workOrderId}/costs

## Inspections Service
- POST /api/v1/inspection-templates
- GET /api/v1/inspection-templates
- GET /api/v1/inspection-templates/{templateId}
- PATCH /api/v1/inspection-templates/{templateId}

- POST /api/v1/inspections
- GET /api/v1/inspections
- GET /api/v1/inspections/{inspectionId}
- PATCH /api/v1/inspections/{inspectionId}
- POST /api/v1/inspections/{inspectionId}/submit

## Housekeeping Service
- POST /api/v1/housekeeping/tasks/generate
- GET /api/v1/housekeeping/tasks
- PATCH /api/v1/housekeeping/tasks/{taskId}
- POST /api/v1/housekeeping/tasks/{taskId}/assign
- POST /api/v1/housekeeping/tasks/{taskId}/complete

## Maintenance Service
- POST /api/v1/maintenance/tasks
- GET /api/v1/maintenance/tasks
- GET /api/v1/maintenance/tasks/{taskId}
- PATCH /api/v1/maintenance/tasks/{taskId}
- POST /api/v1/maintenance/tasks/{taskId}/complete

- POST /api/v1/maintenance/pm-schedules
- GET /api/v1/maintenance/pm-schedules
- GET /api/v1/maintenance/pm-schedules/{scheduleId}
- PATCH /api/v1/maintenance/pm-schedules/{scheduleId}

- POST /api/v1/assets
- GET /api/v1/assets
- GET /api/v1/assets/{assetId}
- PATCH /api/v1/assets/{assetId}

## Guest Experience Service
- POST /api/v1/guest-issues
- GET /api/v1/guest-issues
- GET /api/v1/guest-issues/{issueId}
- PATCH /api/v1/guest-issues/{issueId}
- POST /api/v1/guest-issues/{issueId}/notify
- POST /api/v1/guest-issues/{issueId}/resolve
- POST /api/v1/guest-issues/{issueId}/follow-up

## Guest Communication Service
- POST /api/v1/guest-requests
- GET /api/v1/guest-requests
- GET /api/v1/guest-requests/{requestId}
- PATCH /api/v1/guest-requests/{requestId}
- POST /api/v1/guest-requests/{requestId}/notify

## Risk & Compliance Service
- POST /api/v1/compliance/checklists
- GET /api/v1/compliance/checklists
- GET /api/v1/compliance/checklists/{checklistId}
- PATCH /api/v1/compliance/checklists/{checklistId}

- POST /api/v1/compliance/audits
- GET /api/v1/compliance/audits
- GET /api/v1/compliance/audits/{auditId}
- PATCH /api/v1/compliance/audits/{auditId}
- POST /api/v1/compliance/audits/{auditId}/close

## Projects Service
- POST /api/v1/projects
- GET /api/v1/projects
- GET /api/v1/projects/{projectId}
- PATCH /api/v1/projects/{projectId}

- POST /api/v1/projects/{projectId}/snags
- GET /api/v1/projects/{projectId}/snags
- PATCH /api/v1/projects/{projectId}/snags/{snagId}

## Food & Beverage Service
- POST /api/v1/fb/breakfast
- GET /api/v1/fb/breakfast
- PATCH /api/v1/fb/breakfast/{recordId}

## Corporate Service
- POST /api/v1/corporate/suppliers
- GET /api/v1/corporate/suppliers
- GET /api/v1/corporate/suppliers/{supplierId}
- PATCH /api/v1/corporate/suppliers/{supplierId}

- POST /api/v1/corporate/contracts
- GET /api/v1/corporate/contracts
- GET /api/v1/corporate/contracts/{contractId}
- PATCH /api/v1/corporate/contracts/{contractId}

- POST /api/v1/corporate/orders
- GET /api/v1/corporate/orders
- GET /api/v1/corporate/orders/{orderId}
- PATCH /api/v1/corporate/orders/{orderId}

- POST /api/v1/corporate/capex
- GET /api/v1/corporate/capex
- GET /api/v1/corporate/capex/{capexId}
- PATCH /api/v1/corporate/capex/{capexId}

## Energy & Sustainability Service
- POST /api/v1/energy/kpis
- GET /api/v1/energy/kpis
- GET /api/v1/energy/kpis/{kpiId}
- PATCH /api/v1/energy/kpis/{kpiId}

## Audit & History
- GET /api/v1/audit/logs
- GET /api/v1/audit/logs/{logId}
- GET /api/v1/audit/history
- GET /api/v1/audit/history/{historyId}
