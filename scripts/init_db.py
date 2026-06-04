import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = ROOT / "alembic.ini"


async def initialize_database():
    """Apply Alembic migrations to initialize the database schema."""
    try:
        logger.info("Applying Alembic migrations...")
        alembic_cfg = Config(str(ALEMBIC_INI))
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema is up to date!")
    except Exception as e:
        logger.error(f"Error applying migrations: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(initialize_database())
