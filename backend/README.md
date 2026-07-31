# AI-Powered BI Platform - Backend

This is the backend service for the AI-Powered Business Intelligence & Decision Support Platform, built using FastAPI.

## Database Migrations

We use **Alembic** alongside **SQLAlchemy** to manage database schema updates.

### Creating Migrations

When you add or modify a SQLAlchemy model under `app/infrastructure/db/` (and ensure it is imported in `alembic/env.py`), generate a new migration scripts revision:

```bash
alembic revision --autogenerate -m "description_of_changes"
```

### Running Migrations (Local)

To apply database migration scripts and bring your database schema up-to-date:

```bash
alembic upgrade head
```

To downgrade/rollback the database schema by one revision:

```bash
alembic downgrade -1
```

---

## Running with Docker Compose

To spin up the containerized application (backend service + PostgreSQL database) and apply migrations:

1. **Build and start the container stack:**
   ```bash
   docker compose up --build
   ```

2. **Verify current service health:**
   Open a browser or run curl target: `http://localhost:8000/health` (verify HTTP 200 OK).

3. **Run database migrations within the container:**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

