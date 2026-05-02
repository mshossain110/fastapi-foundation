from typing import Optional
from dependency_injector import containers, providers
from fastapi_foundation.data.db.models.mongo_con_details import MongoConDetails
from fastapi_foundation.data.db.mongo.mongo_client import MongoDbClient

class BaseDiContainer(containers.DeclarativeContainer):
    # Create a resource provider that can be overridden
    mongo_db_client = providers.Resource(lambda: None)
