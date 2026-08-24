from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# NullPool: a pooled connection is bound to whichever event loop first used
# it, and this app has repeatedly ended up with more than one in play
# (FastAPI's TestClient's own portal loop vs. pytest-asyncio's, or a
# TestClient used without a `with` block spinning up a fresh loop per
# call) — each time, a later request reusing a pooled connection from a
# different loop gets asyncpg's "cannot perform operation: another
# operation is in progress". NullPool opens a fresh connection per
# checkout and closes it on release, so no connection ever outlives the
# single async call that created it — correctness over pooling
# performance, appropriate for this app's current traffic level. Revisit
# if/when connection-per-request overhead actually matters.
engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
