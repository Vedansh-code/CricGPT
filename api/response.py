from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class MetaModel(BaseModel):
    count: int
    limit: Optional[int] = None

class EnvelopeResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: Optional[MetaModel] = None
