from functools import partial
from typing import Any, Callable, Optional, Sequence
from abc import ABC, abstractmethod
from fastapi import FastAPI
from fastapi_foundation.data.db.models.mongo_con_details import MongoConDetails
from fastapi_foundation.di.containers import BaseDiContainer
from fastapi_foundation.utils.logger_utils import setup_logging
from pydantic_settings import BaseSettings


async def init_mongo_database(container: BaseDiContainer) -> None:
    """Initialize database connection."""
    db_client = container.mongo_db_client()
    print(f"Mongodb client on base app: {db_client}")
    if db_client is not None:
        await db_client.connect()


async def close_mongo_database(container: BaseDiContainer) -> None:
    """Close database connection."""
    db_client = container.mongo_db_client()
    if db_client is not None:
        await db_client.close()


class FastAPIFoundation(FastAPI, ABC):

    @abstractmethod
    def get_settings(self) -> BaseSettings:
        pass

    @abstractmethod
    def get_modules(self) -> list[str]:
        pass

    @abstractmethod
    def get_container(self) -> BaseDiContainer:
        pass

    @property
    @abstractmethod
    def app_name(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def app_description(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def is_debug(self) -> Optional[bool]:
        pass

    @property
    @abstractmethod
    def is_prod(self) -> bool:
        pass

    @abstractmethod
    def on_startup(self) -> Optional[Sequence[Callable[[], Any]]]:
        pass

    @abstractmethod
    def on_shutdown(self) -> Optional[Sequence[Callable[[], Any]]]:
        pass

    def __init__(self, settings: Optional[BaseSettings] = None):
        print("testing commimng super")
        if settings is None:
            settings = self.get_settings()

        # Setup logging
        logger = setup_logging(settings)

        # Create DI container
        container = self.get_container()

        on_startup = []
        on_shutdown = []

        if container.mongo_db_client:
            on_startup.append(partial(init_mongo_database, container))
            on_shutdown.append(partial(close_mongo_database, container))

        if self.on_startup():
            on_startup.extend(self.on_startup())

        if self.on_shutdown():
            on_shutdown.extend(self.on_shutdown())

        super().__init__(
            title=self.app_name if self.app_name else "Unknown App",
            debug=self.is_debug if self.is_debug else False,
            description=self.app_description if self.app_description else "No description",
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            docs_url=None if self.is_prod else '/docs',
        )

        # Configure container with settings
        container.config.from_pydantic(settings)

        # Wire container to application
        self.container = container
        self.logger = logger
        # Wire up all modules that need DI
        container.wire(
            modules=self.get_modules(),
        )
