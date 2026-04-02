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
