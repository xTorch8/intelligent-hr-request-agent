import logging
from typing import AsyncGenerator, Optional

from ..agents.agent import Agent
from ..models.agent_model import AgentQueryRequest, AgentQueryResponse
from ..models.api_model import APIResponseModel
from ..models.auth_model import UserPayload


class AgentService:
    def __init__(self):
        self._agent = Agent()

    def ask(self, request: AgentQueryRequest, current_user: Optional[UserPayload] = None) -> APIResponseModel[AgentQueryResponse]:
        logging.info(f"[INFO][agent_service.py][ask] Processing query for Agent: '{request.query}'")
        try:
            agent_response = self._agent.ask(request, current_user = current_user)
            return APIResponseModel(
                message = "Agent chat response generated successfully",
                payload = agent_response
            )
        except Exception as e:
            logging.error(f"[ERROR][agent_service.py][ask] Failed to execute agent query. Error: {e}")
            return APIResponseModel(
                error = str(e),
                is_success = False,
                status_code = 500,
                message = "Error executing agent query"
            )

    async def stream_ask(self, request: AgentQueryRequest, current_user: Optional[UserPayload] = None) -> AsyncGenerator[str, None]:
        logging.info(f"[INFO][agent_service.py][stream_ask] Streaming agent response for query: '{request.query}'")
        async for chunk in self._agent.stream_ask(request, current_user = current_user):
            yield chunk
