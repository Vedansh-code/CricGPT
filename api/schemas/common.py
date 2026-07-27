from typing import Optional
from pydantic import BaseModel

class ErrorDetails(BaseModel):
    type: str
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetails
