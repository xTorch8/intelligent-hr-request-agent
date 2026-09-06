from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None

class AgentQueryRequest(BaseModel):
    query: str
    policy_id: Optional[str] = None
    chat_history: Optional[List[ChatMessage]] = []


class AgentQueryResponse(BaseModel):
    query: str
    answer: str
    model_used: str
    chat_history: List[ChatMessage] = []
