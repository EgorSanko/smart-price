"""Dev-only: create all tables from SQLAlchemy models, then stamp alembic head."""
import asyncio
from app.db.base import Base
from app.db import models  # noqa: F401
from app.db.session import engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        await conn.run_sync(Base.metadata.create_all)
    print("tables created")


if __name__ == "__main__":
    asyncio.run(main())
