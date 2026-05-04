# Testing

Contents:
- Test strategy
- Coverage targets
- Quality gates

## Baseline Commands
- Run all tests: `make test`
- Run all coverage reports: `make test-coverage`
- Run lint checks: `make lint`
- Run full quality gate (lint + coverage): `make quality`
- Frontend unit tests (watch): `cd fronend && npm test`
- Frontend unit tests (single run): `cd fronend && npm run test:run`
- Frontend unit test coverage: `cd fronend && npm run test:coverage`
- Frontend lint + coverage (CI style): `cd fronend && npm run test:ci`
- Backend unit tests: `cd backend/services/identity_service && python3 -m pytest`

## Coverage Gates
- Backend: minimum `60%` enforced by `pytest` (`--cov-fail-under=60`).
- Frontend: minimum `50%` enforced by Vitest coverage thresholds.

## Coverage Exclusions
- Backend excludes test files, migrations, config files, `manage.py`, and `__init__.py` from coverage.
- Frontend excludes test harness files and type/bootstrap boilerplate (`src/test/**`, `*.d.ts`, `src/main.tsx`).
