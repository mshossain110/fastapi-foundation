from datetime import datetime
from typing import Generic, Type, TypeVar, Optional, List, Any, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi_foundation.data.db.models.mongo_base_model import MongoBaseModel
from fastapi_foundation.data.db.mongo.mongo_client import MongoDbClient
from fastapi_foundation.data.repositories.base_repository import BaseRepository

T = TypeVar("T", bound=MongoBaseModel)


class BaseMongoRepository(BaseRepository[T, str], Generic[T]):
    """
    Generic async repository for **MongoDB**.

    Implements :class:`~fastapi_foundation.data.repositories.base_repository.BaseRepository`
    using Motor (async PyMongo driver).

    Filter conventions
    ------------------
    ``filter_query`` is a standard **MongoDB query dict**:

    .. code-block:: python

        products = await repo.find_many(
            filter_query={"category": "electronics", "price": {"$lt": 500}},
            skip=0,
            limit=20,
            sort_by=[("price", 1)],
        )
    """

    def __init__(
        self, db_client: MongoDbClient, collection_name: str, model_class: Type[T]
    ):
        self.db_client = db_client
        self.collection_name = collection_name
        self.model_class = model_class

    @property
    def collection(self) -> AsyncIOMotorCollection:  # type: ignore
        return self.db_client.db[self.collection_name]

    async def create(self, data: T) -> str:
        """Create a new document."""
        result = await self.collection.insert_one(data.to_mongo())
        return str(result.inserted_id)

    async def find_by_id(self, id: str) -> Optional[T]:
        """Find a document by its id."""
        try:
            object_id = ObjectId(id)
        except Exception:
            # If the id is invalid, return None
            return None

        document = await self.collection.find_one({"_id": object_id})
        if document:
            return self.model_class.from_mongo(document)
        return None

    async def find_one(self, filter_query: Optional[Dict[str, Any]] = None) -> Optional[T]:
        """Find one document by filter."""
        document = await self.collection.find_one(filter_query or {})
        if document:
            return self.model_class.from_mongo(document)
        return None

    async def find_many(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: Optional[int] = 100,
        sort_by: Optional[List[tuple]] = None,
    ) -> List[T]:
        """Find many documents by filter."""
        # print(filter_query)
        cursor = self.collection.find(filter_query or {}).skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort_by:
            cursor = cursor.sort(sort_by)
        documents = await cursor.to_list(length=None)
        return [self.model_class.from_mongo(doc) for doc in documents]

    async def update_by_id(self, id: str, data: T) -> bool:
        """Update document by ID."""
        try:
            update_data = data.to_mongo()
            update_data["updated_at"] = datetime.now()
            # Remove '_id' from update_data if present
            update_data.pop("_id", None)
            result = await self.collection.update_one(
                {"_id": ObjectId(id)}, {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def delete_by_id(self, id: str) -> bool:
        """Delete document by ID."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def count(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching filter."""
        return await self.collection.count_documents(filter_query or {})

    async def find_many_random(
        self,
        filter_query: Dict[str, Any],
        limit: Optional[int] = 100,
        sort_by: Optional[List[tuple]] = None,
    ) -> List[T]:

        pipeline = []
        pipeline.append({"$match": filter_query})

        if limit:
            pipeline.append({"$sample": {"size": limit}})

        cursor = self.collection.aggregate(pipeline)
        if sort_by:
            cursor = cursor.sort(sort_by)
        documents = await cursor.to_list(length=limit)
        return [self.model_class.from_mongo(doc) for doc in documents]
