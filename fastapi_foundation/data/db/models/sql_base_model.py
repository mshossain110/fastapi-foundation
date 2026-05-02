import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SqlDeclarativeBase(DeclarativeBase):
    """
    Project-wide SQLAlchemy declarative base.

    All SQLAlchemy ORM models must inherit from ``SqlBaseModel`` (which
    inherits this class) so that ``SqlClient.create_all()`` can discover
    every table automatically.
    """


class SqlBaseModel(SqlDeclarativeBase):
    """
    Abstract SQLAlchemy ORM base model.

    Provides three common columns present on every table:

    - ``id``         – UUID primary key (string representation, 36 chars).
    - ``created_at`` – timestamp set by the DB server on INSERT.
    - ``updated_at`` – timestamp updated by the DB server on every UPDATE.

    Usage
    -----
    .. code-block:: python

        from fastapi_foundation.data.db.models.sql_base_model import SqlBaseModel
        from sqlalchemy.orm import Mapped, mapped_column
        from sqlalchemy import String

        class Product(SqlBaseModel):
            __tablename__ = "products"

            name:  Mapped[str]   = mapped_column(String(255))
            price: Mapped[float]
    """

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
