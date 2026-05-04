# Backend Architecture

This backend follows a microservices architecture using Django and Django REST Framework, implemented with Clean Architecture and the Unit of Work pattern.

## Structure
- shared: Cross-service building blocks (kernel, config, libs)
- services: Each microservice lives here

## Service Template
Use `backend/services/service_template` to scaffold new services.

Each service follows:
- domain: Entities, value objects, domain rules
- application: Use cases, services, interfaces (ports)
- infrastructure: ORM, external APIs (email/WhatsApp), integrations
- interfaces: REST API controllers/views (DRF)
- config: Django settings, urls, wsgi/asgi
- tests: Unit and integration tests

## Dependency Rule
- Domain has no dependencies on other layers.
- Application depends only on domain and defined ports.
- Infrastructure implements ports and depends on application/domain.
- Interfaces depend on application and domain.

## Unit of Work
All transactional operations should use a Unit of Work abstraction located in the application layer and implemented in infrastructure.

## Docker (Dev)
From repo root:
- Build and run: `docker compose up --build`
- App: http://localhost:8000

Postgres is included via Docker in both dev and prod paths.

## Admin Bootstrap
Run the admin creation script:
- `docker compose run --rm identity_service python scripts/create_admin.py`

Optional CLI flags:
- `--org-id` (use existing org)
- `--org-name`
- `--email`
- `--display-name`
- `--password`
- `--role` (e.g. `admin` or `super admin`)

Override defaults using env vars:
- `ADMIN_ORG_ID`
- `ADMIN_ORG_NAME`
- `ADMIN_EMAIL`
- `ADMIN_DISPLAY_NAME`
- `ADMIN_PASSWORD`
- `ADMIN_ROLE`
