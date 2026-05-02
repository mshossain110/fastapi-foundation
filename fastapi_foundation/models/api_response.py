from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel
T = TypeVar('T')


class ErrorItem(BaseModel):
    message: Optional[str] = None

    class Config:
        populate_by_name = True
        def alias_generator(s): return s.lower()


class ErrorDescription(BaseModel):
    errors: Optional[List[Optional[ErrorItem]]] = None

    class Config:
        populate_by_name = True
        def alias_generator(s): return s.lower()


class Error(BaseModel):
    message: Optional[str] = None
    title: Optional[str] = None
    description: Optional[ErrorDescription] = None

    class Config:
        populate_by_name = True
        def alias_generator(s): return s.lower()


class ApiResponse(BaseModel, Generic[T]):
    status: Optional[str] = None
    code: Optional[int] = None
    error: Optional[Error] = None
    data: Optional[T] = None

    class Config:
        populate_by_name = True
        def alias_generator(s): return s.lower()
