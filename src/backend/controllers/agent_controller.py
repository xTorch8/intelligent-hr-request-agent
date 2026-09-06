from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..models.agent_model import AgentQueryRequest, AgentQueryResponse
from ..models.api_model import APIResponseModel
from ..models.auth_model import UserPayload
from ..services.agent_service import AgentService
from ..utils.security import get_current_user

router = APIRouter(
    prefix = "/api/agent",
    tags = ["agent"]
)

agent_service = AgentService()


@router.post("/chat", response_model = APIResponseModel[AgentQueryResponse])
async def chat_with_agent(
    request: AgentQueryRequest,
    current_user: UserPayload = Depends(get_current_user)
):
    return agent_service.ask(request)


@router.post("/chat/stream")
async def chat_with_agent_stream(
    request: AgentQueryRequest,
    current_user: UserPayload = Depends(get_current_user)
):
    return StreamingResponse(
        agent_service.stream_ask(request),
        media_type = "text/event-stream"
    )