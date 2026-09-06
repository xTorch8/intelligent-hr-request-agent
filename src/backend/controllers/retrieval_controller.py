from fastapi import APIRouter, Depends
from typing import Optional

from ..models.api_model import APIResponseModel
from ..models.retrieval_model import SearchQueryRequest, SearchQueryResponse
from ..services.retrieval_service import RetrievalService

router = APIRouter(
    prefix = "/api/retrieval",
    tags = ["retrieval"]
)

retrieval_service = RetrievalService()

@router.get("/", response_model = APIResponseModel[Optional[SearchQueryResponse]])
async def search_policy_chunks(request: SearchQueryRequest = Depends()):
    return retrieval_service.retrieve(request)
