from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Ensure project root is on sys.path for imports.
# In Docker, env.py lives at /app/alembic/env.py and project root is /app.
# Create a fake 'backend' package alias pointing to /app so imports like
# 'from backend.database import Base' work in the container.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# If running in container (/app/alembic/env.py), create a 'backend' alias
# that points to the `backend` package directory when it exists (e.g. /app/backend),
# otherwise point to the project root (/app). This makes imports like
# 'from backend.database import Base' resolve in both layouts.
if os.path.basename(PROJECT_ROOT) == 'app' and '/app' in os.path.abspath(__file__):
    import importlib.util
    spec = importlib.util.spec_from_loader('backend', loader=None)
    if spec is not None:
        backend_module = importlib.util.module_from_spec(spec)
        # Prefer the explicit backend package directory if present
        backend_dir = os.path.join(PROJECT_ROOT, 'backend')
        if os.path.isdir(backend_dir):
            backend_module.__path__ = [backend_dir]
        else:
            backend_module.__path__ = [PROJECT_ROOT]
        sys.modules['backend'] = backend_module

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
try:
    from backend.database import Base  # type: ignore
    from backend import models  # noqa: F401
except ModuleNotFoundError:
    # Fallback: load the backend package and database module directly from files.
    import importlib.util

    backend_dir = os.path.join(PROJECT_ROOT, 'backend')
    db_path = os.path.join(backend_dir, 'database.py')

    # Create a package module for 'backend' if not present
    if 'backend' not in sys.modules:
        spec_pkg = importlib.util.spec_from_loader('backend', loader=None)
        if spec_pkg is not None:
            pkg = importlib.util.module_from_spec(spec_pkg)
            pkg.__path__ = [backend_dir]
            sys.modules['backend'] = pkg

    # Load backend.database from file
    if os.path.isfile(db_path):
        spec_db = importlib.util.spec_from_file_location('backend.database', db_path)
        if spec_db is not None:
            module_db = importlib.util.module_from_spec(spec_db)
        sys.modules['backend.database'] = module_db
        # execute the module to populate attributes like Base
        spec_db.loader.exec_module(module_db)  # type: ignore
        Base = getattr(module_db, 'Base')
    else:
        raise

    # Ensure models package is importable (best-effort)
    try:
        from backend import models  # noqa: F401
    except Exception:
        pass

target_metadata = Base.metadata

# Set database URL from environment variable
database_url = os.getenv("DATABASE_URL", "sqlite:///./exchange.db")
config.set_main_option("sqlalchemy.url", database_url)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
