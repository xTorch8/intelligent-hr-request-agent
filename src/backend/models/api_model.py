from pydantic import BaseModel
from typing import Optional, Generic, TypeVar

T = TypeVar("T")

class APIResponseModel(BaseModel, Generic[T]):
    error: Optional[str] = None
    is_success: Optional[bool] = True
    status_code: Optional[int] = 200
    message: Optional[str] = None
    payload: Optional[T] = None