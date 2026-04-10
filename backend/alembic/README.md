# Alembic Migrations

This directory contains database migrations for the Inventory Management System.

## Setup

1. Ensure PostgreSQL is running and the database exists
2. Set the DATABASE_URL in `.env` file
3. Run migrations with: `alembic upgrade head`

## Common Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current migration status
alembic current

# View migration history
alembic history
```

## Adding New Models

1. Add the new model to `app/models/`
2. Import the model in `app/models/__init__.py`
3. Update `alembic/env.py` to include the model in target_metadata
4. Generate migration: `alembic revision --autogenerate -m "Add <model_name>"`
5. Review the generated migration file
6. Apply: `alembic upgrade head`
