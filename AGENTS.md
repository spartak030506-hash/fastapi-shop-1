# Repository Guidelines

## Project Structure & Modules
- `app/`: FastAPI app with layers: `api/v1` routers + dependencies, `core` config/security/database, `models` (SQLAlchemy), `schemas` (Pydantic), `repositories` (DB access), `services` (business logic), `utils` (validators).
- `alembic/` + `alembic.ini`: migrations; keep revisions in `alembic/versions`.
- `tests/`: pytest suites split by domain (`test_api`, `test_repositories`, `test_security`, `test_services`); fixtures live in `tests/conftest.py`.
- `docker/`: container tooling placeholder; add compose files here if used.
- Config uses `.env` (see `app/core/config.py`) for DB URL and JWT secrets; never commit secrets.

## Build, Run, and Development Commands
- Install deps: `pip install -r requirements.txt` (use a venv).
- Run app locally: `uvicorn app.main:app --reload` (serves `/docs`, `/redoc`, `/health`).
- Migrations: `alembic upgrade head` (apply) / `alembic revision -m "message" --autogenerate` (create).
- Lint/format (optional tools listed in `requirements.txt`): `flake8 app tests`, `black app tests`, `isort app tests`, `mypy app`.
- Tests: `pytest` (full), `pytest -m unit` / `-m integration` to scope markers; add `--cov=app` for coverage.

## Coding Style & Naming
- Python 3.11+ style with 4-space indent, type hints everywhere, and descriptive docstrings (follow existing Russian-language tone).
- Use `snake_case` for modules/functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for settings/constants.
- Keep request/response models in `app/schemas`, DB logic in `app/repositories`, and orchestration in `app/services`; avoid cross-layer leakage.
- Prefer deterministic validators (see `app/utils/validators.py`) and centralized security helpers in `app/core/security.py`.

## Testing Guidelines
- Async tests rely on pytest-asyncio; use provided fixtures (`db_session`, `test_user`, etc.) from `tests/conftest.py`.
- Name tests `test_<feature>.py`; mark appropriately (`@pytest.mark.unit`, `integration`, `e2e`).
- For DB-affecting tests, commit within the test if asserting persisted state (mirrors existing repository tests).
- Add coverage for new endpoints via API tests and repository/service behaviors with integration tests.

## Commit & Pull Request Guidelines
- Commit messages in this repo are short, descriptive, and often Russian (e.g., `Модернизация security: PyJWT + bcrypt напрямую`); keep them under ~72 chars and prefer the imperative/present tense.
- Group related changes per commit; include migrations and schema updates together.
- PRs should include: summary of change, linked issue/task, test evidence (`pytest ...` output), migration notes (new/modified revisions), and any local run commands used.
- Keep diffs minimal: update docs/config samples when behavior changes; add screenshots only if touching docs or interactive clients.

## Security & Configuration Tips
- Populate `.env` with strong `SECRET_KEY`, `REFRESH_TOKEN_SECRET`, and a full `DATABASE_URL`; set `DB_ECHO=False` outside local debugging.
- Review CORS settings in `app/main.py` before exposing publicly; restrict `allow_origins` in production.
- Rotate JWT secrets on compromise and expire refresh tokens accordingly (`REFRESH_TOKEN_EXPIRE_DAYS`).
