from pydantic import BaseModel
from typing import Optional

class GuardrailRequest(BaseModel):
    input: str

class GuardrailResponse(BaseModel):
    is_safe: bool
    error: Optional[str] = None