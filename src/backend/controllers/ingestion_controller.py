from fastapi import APIRouter

from ..models.ingestion_model import IngestDocumentRequest
from ..services.ingestion_service import IngestionService

router = APIRouter(
    prefix = "/api/ingestion",
    tags = ["ingestion"]
)

ingestion_service = IngestionService()

@router.post("/")
async def ingest_document(request: IngestDocumentRequest):
    return ingestion_service.ingest_document(request)

