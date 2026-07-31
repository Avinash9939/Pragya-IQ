import sys
from os.path import abspath, dirname
# Add the project root to sys.path so alembic can find backend/app
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import our config and Base metadata
from app.core.config import settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.models.dataset_model import DatasetModel
from app.infrastructure.db.models.cleaning_log_model import CleaningLogModel
from app.infrastructure.db.models.kpi_result_model import KpiResultModel
from app.infrastructure.db.models.ml_model import MlRunModel, MlPredictionModel
from app.infrastructure.db.models.chat_model import ChatSessionModel, ChatMessageModel
from app.infrastructure.db.models.ai_output_model import AiOutputModel
from app.infrastructure.db.models.report_model import ReportModel
from app.infrastructure.db.models.activity_log_model import ActivityLogModel
from app.infrastructure.db.models.system_setting_model import SystemSettingModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set DB url dynamically from configured settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

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
