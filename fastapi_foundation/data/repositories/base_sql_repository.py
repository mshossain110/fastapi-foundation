from datetime import datetime
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select

from fastapi_foundation.data.db.models.sql_base_model import SqlBaseModel
from fastapi_foundation.data.db.sql.sql_client import SqlClient
from fastapi_foundation.data.repositories.base_repository import BaseRepository

T = TypeVar("T", bound=SqlBaseModel)


class BaseSqlRepository(BaseRepository[T, str], Generic[T]):
    """
    Generic async repository for **SQL databases** (PostgreSQL, MySQL).

    Built on SQLAlchemy async and works with any model that extends
    :class:`~fastapi_foundation.data.db.models.sql_base_model.SqlBaseModel`.

    Parameters
    ----------
    db_client:
        Connected :class:`~fastapi_foundation.data.db.sql.sql_client.SqlClient` instance.
    model_class:
        The SQLAlchemy ORM class this repository manages.

    Filter conventions
    ------------------
    ``filter_query`` is a **list of SQLAlchemy column expressions**:

    .. code-block:: python

        from myapp.models import Product

        repo = ProductRepository(db_client, Product)

        # Single condition
        product = await repo.find_one([Product.sku == "ABC-123"])

        # Multiple conditions (AND)
        products = await repo.find_many(
            filter_query=[Product.category == "electronics", Product.price < 500],
            skip=0,
            limit=20,
            sort_by=[Product.price.asc()],
        )

    Example — defining a concrete repository
    -----------------------------------------
    .. code-block:: python

        from sqlalchemy.orm import Mapped, mapped_column
        from sqlalchemy import String, Numeric
        from fastapi_foundation.data.db.models.sql_base_model import SqlBaseModel
        from fastapi_foundation.data.repositories.base_sql_repository import BaseSqlRepository

        class Product(SqlBaseModel):
            __tablename__ = "products"
            name:  Mapped[str]   = mapped_column(String(255))
            price: Mapped[float] = mapped_column(Numeric(10, 2))

        class ProductRepository(BaseSqlRepository[Product]):
            def __init__(self, db_client):
                super().__init__(db_client, Product)
    """

    def __init__(self, db_client: SqlClient, model_class: Type[T]) -> None:
        self.db_client = db_client
        self.model_class = model_class

    async def create(self, data: T) -> str:
        """
        Persist *data* and return its ``id``.

        The ``id`` field is populated by the model's default factory before
        the INSERT, so the returned value is always set.
        """
        async with self.db_client.session() as session:
            session.add(data)
            await session.commit()
            await session.refresh(data)
            return str(data.id)

    async def find_by_id(self, id: str) -> Optional[T]:
        """Return the record whose primary key equals *id*, or ``None``."""
        async with self.db_client.session() as session:
            return await session.get(self.model_class, id)

    async def find_one(
        self, filter_query: Optional[List[Any]] = None
    ) -> Optional[T]:
        """
        Return the first record matching *filter_query*, or ``None``.

        Parameters
        ----------
        filter_query:
            List of SQLAlchemy column expressions combined with AND.
            Pass ``None`` or ``[]`` to match any record.
        """
        async with self.db_client.session() as session:
            stmt = select(self.model_class)
            if filter_query:
                stmt = stmt.where(*filter_query)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def find_many(
        self,
        filter_query: Optional[List[Any]] = None,
        skip: int = 0,
        limit: Optional[int] = 100,
        sort_by: Optional[List[Any]] = None,
    ) -> List[T]:
        """
        Return records matching *filter_query* with optional pagination and ordering.

        Parameters
        ----------
        filter_query:
            List of SQLAlchemy column expressions combined with AND.
        skip:
            Number of rows to skip (OFFSET).
        limit:
            Maximum rows to return. Pass ``None`` for no limit.
        sort_by:
            List of SQLAlchemy order-by clauses, e.g.
            ``[Product.price.asc(), Product.name.desc()]``.
        """
        async with self.db_client.session() as session:
            stmt = select(self.model_class)
            if filter_query:
                stmt = stmt.where(*filter_query)
            if sort_by:
                stmt = stmt.order_by(*sort_by)
            stmt = stmt.offset(skip)
            if limit is not None:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_by_id(self, id: str, data: T) -> bool:
        """
        Overwrite the record identified by *id* with the fields in *data*.

        ``id`` and ``created_at`` are never overwritten.

        Returns ``True`` when a matching record was found and updated.
        """
        async with self.db_client.session() as session:
            existing = await session.get(self.model_class, id)
            if existing is None:
                return False

            skip_cols = {"id", "created_at"}
            for col in self.model_class.__table__.columns.keys():
                if col in skip_cols:
                    continue
                new_val = getattr(data, col, None)
                if new_val is not None:
                    setattr(existing, col, new_val)

            existing.updated_at = datetime.now()
            await session.commit()
            return True

    async def delete_by_id(self, id: str) -> bool:
        """
        Delete the record identified by *id*.

        Returns ``True`` when a record was actually removed.
        """
        async with self.db_client.session() as session:
            existing = await session.get(self.model_class, id)
            if existing is None:
                return False
            await session.delete(existing)
            await session.commit()
            return True

    async def count(self, filter_query: Optional[List[Any]] = None) -> int:
        """
        Return the number of records matching *filter_query*.

        Parameters
        ----------
        filter_query:
            List of SQLAlchemy column expressions combined with AND.
            Pass ``None`` or ``[]`` to count all records.
        """
        async with self.db_client.session() as session:
            stmt = select(func.count()).select_from(self.model_class)
            if filter_query:
                stmt = stmt.where(*filter_query)
            result = await session.execute(stmt)
            return result.scalar() or 0
