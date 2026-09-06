from fastapi import APIRouter, Depends

from ..models.auth_model import UserPayload
from ..models.ingestion_model import IngestDocumentRequest
from ..services.ingestion_service import IngestionService
from ..utils.security import get_current_user

router = APIRouter(
    prefix = "/api/ingestion",
    tags = ["ingestion"]
)

ingestion_service = IngestionService()


@router.post("/")
async def ingest_document(
    request: IngestDocumentRequest,
    current_user: UserPayload = Depends(get_current_user)
):
    return ingestion_service.ingest_document(request)
