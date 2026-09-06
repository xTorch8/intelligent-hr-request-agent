from typing import Optional
from fastapi import APIRouter, Depends

from ..models.api_model import APIResponseModel
from ..models.auth_model import UserPayload
from ..models.retrieval_model import SearchQueryRequest, SearchQueryResponse
from ..services.retrieval_service import RetrievalService
from ..utils.security import get_current_user

router = APIRouter(
    prefix = "/api/retrieval",
    tags = ["retrieval"]
)

retrieval_service = RetrievalService()

@router.get("/", response_model = APIResponseModel[Optional[SearchQueryResponse]])
async def search_policy_chunks(
    request: SearchQueryRequest = Depends(),
    current_user: UserPayload = Depends(get_current_user)
):
    return retrieval_service.retrieve(request)
