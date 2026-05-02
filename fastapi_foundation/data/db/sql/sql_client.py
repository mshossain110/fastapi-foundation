from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastapi_foundation.data.db.models.sql_base_model import SqlDeclarativeBase


class SqlClient:
    """
    Async SQLAlchemy client — works with **PostgreSQL** and **MySQL**.

    The database backend is selected entirely by the connection URL:

    - **PostgreSQL** (via asyncpg)::

        postgresql+asyncpg://user:password@host:5432/dbname

    - **MySQL** (via aiomysql)::

        mysql+aiomysql://user:password@host:3306/dbname

    Install the matching async driver in your service:

    .. code-block:: bash

        pip install asyncpg          # PostgreSQL
        pip install aiomysql         # MySQL

    Parameters
    ----------
    url:
        SQLAlchemy async database URL.
    echo:
        When ``True`` every SQL statement is logged (useful during development).
    **engine_kwargs:
        Any extra keyword arguments forwarded to :func:`create_async_engine`
        (e.g. ``pool_size``, ``max_overflow``, ``pool_recycle``).

    Usage
    -----
    .. code-block:: python

        client = SqlClient("postgresql+asyncpg://user:pass@localhost/mydb", echo=False)

        # Startup
        await client.connect()

        # Use a session
        async with client.session() as session:
            result = await session.execute(select(Product))

        # Shutdown
        await client.close()
    """

    def __init__(self, url: str, echo: bool = False, **engine_kwargs: Any) -> None:
        self._url = url
        self._echo = echo
        self._engine_kwargs = engine_kwargs
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def connect(self) -> None:
        """Create the async engine and session factory."""
        if self._engine is None:
            self._engine = create_async_engine(
                self._url,
                echo=self._echo,
                **self._engine_kwargs,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    async def close(self) -> None:
        """Dispose the engine and release all pooled connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    async def create_all(self) -> None:
        """
        Create all tables registered on ``SqlDeclarativeBase``.

        Useful for development / tests. For production prefer Alembic
        migrations.
        """
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        async with self._engine.begin() as conn:
            await conn.run_sync(SqlDeclarativeBase.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager that yields a :class:`AsyncSession`.

        Automatically rolls back on exception and closes the session
        when the ``async with`` block exits.

        .. code-block:: python

            async with client.session() as session:
                session.add(product)
                await session.commit()
        """
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
