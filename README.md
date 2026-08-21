# Job Market Oracle

Job Market Oracle is a prototype that will predict whether the share of newly published
software-development job postings mentioning a technology skill will increase in the next week.

This initial step contains infrastructure only. It does not yet include job ingestion, database
models, skill matching, indicators, predictions, a scheduler, authentication, or a frontend.

## Technology stack

- Python 3.11
- FastAPI
- SQLAlchemy and Alembic
- PostgreSQL
- Poetry
- pytest
- Docker Compose

## Local setup

1. Copy `.env.example` to `.env` and set a local PostgreSQL password.
2. Install backend dependencies:

   ```bash
   cd backend
   poetry install
   ```

3. Run the application locally:

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

The service will be available at `http://localhost:8000`. Check `GET /health` to verify it is running.

## Run with Docker Compose

```bash
docker compose up --build
```

The example `DATABASE_URL` is written for Compose, where PostgreSQL is reachable as `db`.
For a locally installed database, change the host to `localhost` in your uncommitted `.env` file.

## Run tests

```bash
cd backend
APP_ENV=test DATABASE_URL=postgresql+psycopg://unused:unused@localhost:5432/unused poetry run pytest
```

## Lint and format check

```bash
cd backend
poetry run ruff check .
poetry run ruff format --check .
```
