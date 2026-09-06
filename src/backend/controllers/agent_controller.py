from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..models.agent_model import AgentQueryRequest, AgentQueryResponse
from ..models.api_model import APIResponseModel
from ..services.agent_service import AgentService

router = APIRouter(
    prefix = "/api/agent",
    tags = ["agent"]
)

agent_service = AgentService()


@router.post("/chat", response_model = APIResponseModel[AgentQueryResponse])
async def chat_with_agent(request: AgentQueryRequest):
    return agent_service.ask(request)


@router.post("/chat/stream")
async def chat_with_agent_stream(request: AgentQueryRequest):
    return StreamingResponse(
        agent_service.stream_ask(request),
        media_type = "text/event-stream"
    )