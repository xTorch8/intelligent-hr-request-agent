import asyncio
import logging
from src.backend.models.agent_model import AgentQueryRequest
from src.backend.services.agent_service import AgentService


async def test_agent_sse_stream():
    print("\n==================================================")
    print("      Testing Agent SSE Chat Streaming           ")
    print("==================================================")
    
    agent_service = AgentService()
    request = AgentQueryRequest(
        query = "What is the policy for annual leave duration and notice requirement for employee EMP-0001?"
    )
    
    print(f"\n💬 Query: '{request.query}'")
    print("-" * 60)
    
    async for sse_chunk in agent_service.stream_ask(request):
        print(sse_chunk.strip())


if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO)
    asyncio.run(test_agent_sse_stream())

