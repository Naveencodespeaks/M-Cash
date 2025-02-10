import importlib
import pkgutil
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, MetaData
from alembic import context
from sqlalchemy.ext.declarative import DeclarativeMeta

# Alembic Config object and logging configuration
config = context.config
fileConfig(config.config_file_name)

# Initialize an empty MetaData object
target_metadata = MetaData()

def load_models(package_name: str):
    """Load all modules in the given package and extract metadata."""
    for _, module_name, _ in pkgutil.iter_modules(importlib.import_module(package_name).__path__):
        module = importlib.import_module(f'{package_name}.{module_name}')
        
        # Iterate over attributes in the module
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            
            
            # Check if the attribute is a model class (subclass of DeclarativeMeta)
            if isinstance(attribute, DeclarativeMeta):
                # Add the metadata from this model to the target_metadata
                for table in attribute.metadata.tables.values():
                    if table.name not in target_metadata.tables:
                        table.tometadata(target_metadata)

# Load all models and update target_metadata
load_models('models')

# Alembic environment configurations
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
