from fastapi import APIRouter

from ..models.retrieval_model import SearchQueryRequest, SearchQueryResponse
from ..services.retrieval_service import RetrievalService

router = APIRouter(
    prefix = "/api/retrieval",
    tags = ["retrieval"]
)

retrieval_service = RetrievalService()

@router.post("/", response_model = SearchQueryResponse)
async def search_policy_chunks(request: SearchQueryRequest):
    return retrieval_service.retrieve(request)

