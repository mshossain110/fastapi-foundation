from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")
IDType = TypeVar("IDType")


class BaseRepository(ABC, Generic[T, IDType]):
    """
    Abstract repository interface.

    Concrete implementations target a specific database backend
    (MongoDB, PostgreSQL, MySQL, etc.) while exposing a unified API.

    Type parameters
    ---------------
    T       : The model type returned and accepted by all operations.
    IDType  : The primary-key type (``str`` for MongoDB ObjectId,
              ``str`` UUID for SQL, ``int`` for auto-increment SQL, …).

    Filter conventions
    ------------------
    ``filter_query`` is intentionally typed as ``Any`` because the
    natural filter format differs per backend:

    - **MongoDB** – plain dict, e.g. ``{"status": "active", "age": {"$gt": 18}}``
    - **SQL (SQLAlchemy)** – list of column expressions, e.g.
      ``[User.status == "active", User.age > 18]``

    Each concrete class re-declares the parameter with a more specific
    type so that callers get proper IDE support.
    """

    @abstractmethod
    async def create(self, data: T) -> IDType:
        """Persist *data* and return its primary key."""
        ...

    @abstractmethod
    async def find_by_id(self, id: IDType) -> Optional[T]:
        """Return the record whose primary key equals *id*, or ``None``."""
        ...

    @abstractmethod
    async def find_one(self, filter_query: Any) -> Optional[T]:
        """Return the first record matching *filter_query*, or ``None``."""
        ...

    @abstractmethod
    async def find_many(
        self,
        filter_query: Any,
        skip: int = 0,
        limit: Optional[int] = 100,
        sort_by: Optional[Any] = None,
    ) -> List[T]:
        """Return records matching *filter_query* with optional pagination and ordering."""
        ...

    @abstractmethod
    async def update_by_id(self, id: IDType, data: T) -> bool:
        """
        Overwrite the record identified by *id* with the fields in *data*.

        Returns ``True`` when at least one row was modified.
        """
        ...

    @abstractmethod
    async def delete_by_id(self, id: IDType) -> bool:
        """
        Delete the record identified by *id*.

        Returns ``True`` when a record was actually removed.
        """
        ...

    @abstractmethod
    async def count(self, filter_query: Any) -> int:
        """Return the number of records matching *filter_query*."""
        ...
