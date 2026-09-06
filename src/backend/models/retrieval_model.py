from pydantic import BaseModel
from typing import List, Optional

from .ingestion_model import ChunkMetadata


class SearchQueryRequest(BaseModel):
    query: str
    policy_id: Optional[str] = None


class SearchResultChunk(BaseModel):
    chunk_id: str
    policy_id: str
    chunk_index: int
    content: str
    vector_score: float = 0.0
    text_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    metadata: Optional[ChunkMetadata] = None


class SearchQueryResponse(BaseModel):
    query: str
    results: List[SearchResultChunk]

