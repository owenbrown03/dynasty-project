import asyncio
import sys
from os.path import abspath, dirname
from logging.config import fileConfig
from sqlmodel import SQLModel
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.core.config import settings
from app.models.base import SQLModel

sys.path.insert(0, abspath(dirname(dirname(__file__))))

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
target_metadata = SQLModel.metadata 

def run_migrations_offline() -> None:
    url = settings.DATABASE_URL 
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an AsyncEngine."""
    
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            # run_sync unrolls our synchronous configuration steps across the async connection safely
            await connection.run_sync(do_run_migrations)
        
        await connectable.dispose()

    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()