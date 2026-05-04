# Unit Test Implementation Plan

## 1) Objectives
1. Add reliable unit tests for backend (`Django/DRF`) and frontend (`React/TypeScript`).
2. Protect critical identity flows first (auth, RBAC, user/role/permission management).
3. Enforce coverage and keep tests fast enough for daily development.
4. Ensure all core management modules are covered end-to-end.

## 2) Scope (Phase 1 Testing)
1. Backend unit tests:
- Serializers validation
- Auth utilities and token flow logic
- Permission checks (`_has_permission`, role normalization, admin/super-admin rules)
- Service-layer logic (audit logging service)
- API view behavior with mocked side effects (email sending, invite flow)
2. Frontend unit tests:
- Auth context (`login/logout/fetchMe`)
- User management UI logic (role checks, button visibility, form state)
- Audit log filters and query-param mapping
- API client behavior and error handling
3. Module coverage targets:
- User Management
- Role Management
- Permission Management
- Organization Management
- Property Management
- Department Management
- Audit Logs

## 3) Tooling Plan
1. Backend:
- `pytest`
- `pytest-django`
- `pytest-cov`
- `factory_boy`
- `faker`
2. Frontend:
- `vitest`
- `@testing-library/react`
- `@testing-library/jest-dom`
- `@testing-library/user-event`
- `msw` (mock API)
3. Reporting:
- Coverage reports for backend and frontend
- Minimum threshold gates (start realistic, then raise)

## 4) Directory/Test Structure
1. Backend:
- `backend/services/identity_service/tests/unit/...`
- `backend/services/identity_service/tests/integration/...` (later, not first)
- `conftest.py`, `factories.py`, reusable fixtures
2. Frontend:
- `fronend/src/**/__tests__/*.test.tsx`
- `fronend/src/test/setup.ts`
- `fronend/src/test/mocks/*` (MSW handlers)

## 5) Phase-wise Task Plan
1. Phase A: Foundation Setup
- Add backend test dependencies and `pytest.ini`
- Add frontend Vitest/RTL/MSW setup
- Add baseline test scripts (`make test`, npm scripts)
- Add sample smoke tests (1 backend, 1 frontend)

2. Phase B: Backend Core Unit Tests
- Auth serializer tests (`LoginSerializer`, `RefreshSerializer`, etc.)
- JWT issue/refresh/logout tests (success + failure cases)
- Permission utility tests for role hierarchy
- Invite token and activation path tests (with mocked email)

3. Phase C: Backend API Unit Tests (High-value endpoints)
- `/auth/login`, `/auth/refresh`, `/auth/logout`
- `/me`
- `/users` CRUD permissions
- `/roles`, `/permissions`, mapping endpoints
- Audit log endpoint filters (`actor`, `action`, `target`, date range)

4. Phase D: Frontend Unit Tests
- `authContext` login/logout token mapping
- Login page submit + error states
- User management role-based UI visibility
- Audit logs page filters -> query params
- Protected-route behavior

5. Phase E: Coverage & Quality Gates
- Backend coverage gate (start 60%)
- Frontend coverage gate (start 50%)
- Exclude generated/boilerplate files from coverage
- Add failure on test/lint errors

6. Phase F: Documentation
- Add `docs/10-testing/README.md` with:
- how to run tests
- test conventions
- fixture strategy
- mocking strategy
- coverage policy

## 6) Module Coverage Checklist (Status-Based)
Status tags:
- `Done`: fully covered by implemented tests.
- `In Progress`: partially covered by implemented tests.
- `Pending`: not yet covered by implemented tests.

1. User Management
- [x] `Done` Backend: `GET /users` permission checks + search/page + sorting assertions covered.
- [x] `Done` Backend: `POST /users` create success + active-password validation + duplicate conflict covered.
- [x] `Done` Backend: `GET/PATCH/DELETE /users/<id>` permission paths + super-admin delete constraint covered.
- [x] `Done` Backend: `users/<id>/roles`, `users/<id>/properties`, and `users/<id>/departments` assign/list/remove mappings covered.
- [x] `Done` Frontend: user menu visibility by permission covered.
- [x] `Done` Frontend: user list query-param mapping (`q`, `page`, `sort_by`, `sort_dir`) covered.
- [x] `Done` Frontend: create/edit modal submit + error rendering covered.
- [x] `Done` Frontend: action visibility (invite/suspend/reactivate/delete) by permission/role context covered.

2. Role Management
- [x] `Done` Backend: role list/create/update/delete happy paths and permission checks covered.
- [x] `Done` Backend: duplicate conflict + in-use conflict assertions covered.
- [x] `Done` Frontend: role menu visibility by permission covered.
- [x] `Done` Frontend: role list sorting + pagination behavior covered.
- [x] `Done` Frontend: role create/edit/delete UI action states covered.

3. Permission Management
- [x] `Done` Backend: permission list/create/update/delete happy paths and permission checks covered.
- [x] `Done` Backend: duplicate conflict + in-use conflict assertions covered.
- [x] `Done` Frontend: permission menu visibility by permission covered.
- [x] `Done` Frontend: permission list query-param mapping + sorting covered.
- [x] `Done` Frontend: permission create/edit/delete UI paths covered.

4. Organization Management
- [x] `Done` Backend: `GET/POST/PATCH/DELETE /organizations*` permission + behavior tests covered.
- [x] `Done` Frontend: organization menu/list/create-edit-delete coverage covered.

5. Property Management
- [x] `Done` Backend: `GET/POST/PATCH/DELETE /properties*` permission + behavior tests covered.
- [x] `Done` Frontend: property menu/list/create-edit-delete coverage covered.

6. Department Management
- [x] `Done` Backend: `GET/POST/PATCH/DELETE /departments*` permission + behavior tests covered.
- [x] `Done` Frontend: department menu/list/create-edit-delete coverage covered.

7. Audit Logs
- [x] `Done` Backend: required `org_id`, permission checks, and filters (`actor/action/target/date range`) covered.
- [x] `Done` Backend: explicit pagination/sorting (`created_at`, `action`, `target_type`) assertions covered.
- [x] `Done` Frontend: audit menu visibility + filter-to-query-param mapping covered.
- [x] `Done` Frontend: sort toggle + pagination request mapping assertions covered.

## 7) Acceptance Criteria
1. All tests runnable via single backend and frontend commands.
2. Critical identity paths covered with passing tests.
3. All seven management modules have backend + frontend unit coverage aligned to the matrix in Section 6.
4. Coverage reports generated locally and thresholds enforced (backend 60%, frontend 50%).
5. New PRs fail on test/lint errors and run consistently in Docker.
6. Testing docs available for team onboarding.

## 8) Suggested Timeline
1. Day 1: Phase A
2. Day 2-3: Phase B
3. Day 4-5: Phase C
4. Day 6: Phase D
5. Day 7: Phase E + F
6. Day 8-9: Module coverage completion sweep for all items in Section 6
