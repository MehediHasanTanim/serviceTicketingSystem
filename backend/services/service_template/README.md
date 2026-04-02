# Service Template

This template provides the Clean Architecture layout for a Django microservice.

## Folders
- domain: Entities, value objects, domain services
- application: Use cases, DTOs, ports, Unit of Work
- infrastructure: ORM models, repositories, external adapters
- interfaces: API layer (DRF views, serializers, routers)
- config: Django project settings
- tests: Unit + integration

## Notes
- Keep Django models in infrastructure/db.
- Expose only application use cases to the interface layer.
- Infrastructure implements ports defined in application.
