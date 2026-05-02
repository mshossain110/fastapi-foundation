
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from datetime import timedelta, timezone


class MongoDbClient:
    def __init__(self, url: str, db_name: str):
        self._url = url
        self._db_name = db_name
        self._client: Optional[AsyncIOMotorClient] = None # type: ignore
        self._db: Optional[AsyncIOMotorDatabase] = None # type: ignore

    async def connect(self) -> None:
        """Create database connection."""
        if self._client is None:
            self._client = AsyncIOMotorClient(self._url, 
                           tz_aware=True,
                           tzinfo=timezone(timedelta(hours=-4)))
            self._db = self._client[self._db_name]

    async def close(self) -> None:
        """Close database connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None

    @property
    def db(self) -> AsyncIOMotorDatabase: # type: ignore
        """Get database instance."""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db