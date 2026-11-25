# Changing the database (Alembic migrations)

Since step 27 the backend never deletes your database to change it. Each
change to the tables is a small numbered file in `src/backend/migrations/versions/`.

Run every command from `src/backend`.

## Normal use
Nothing to do. When the server starts it runs `alembic upgrade head`, which
applies any migrations your database doesn't have yet.

An old `nearbyconnect.db` made before step 27 is "adopted": it's marked as
version 0001 and kept as it is, with all its data.

## When you add or change a column
1. Edit the model, e.g. add a field in `models/user.py`.
2. Create the migration (Alembic compares models with your database):
   ```
   alembic revision --autogenerate -m "add bio to users"
   ```
3. Open the new file in `migrations/versions/` and read it. Autogenerate
   can miss renames (it sees "drop column + add column"), so fix those by hand.
4. Apply it: `alembic upgrade head`
5. Run `pytest -q`. `tests/test_migrations.py` fails if models and
   migrations disagree, and CI runs `alembic check` too.

## Useful commands
| Command | What it does |
| --- | --- |
| `alembic current` | which version your database is on |
| `alembic history` | list every migration |
| `alembic downgrade -1` | undo the last migration |
| `alembic upgrade head --sql` | print the SQL without running it |
