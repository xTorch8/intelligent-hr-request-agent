import logging
import math
from typing import Dict, List, Optional

from ..clients.openai_client import OpenAIClient
from ..configs.openai_config import OpenAIConfig
from ..configs.retrieval_config import RetrievalConfig
from ..models.retrieval_model import (
    SearchQueryRequest,
    SearchQueryResponse,
    SearchResultChunk
)
from ..repositories.retrieval_repository import RetrievalRepository


class RetrievalService:
    def __init__(self):
        self._openai_client = OpenAIClient().get_client()
        self._retrieval_repository = RetrievalRepository()
        self._embedding_model = OpenAIConfig.EMBEDDING_MODEL
        self._top_k = RetrievalConfig.TOP_K
        self._fetch_k = RetrievalConfig.FETCH_K

    def retrieve(self, request: SearchQueryRequest) -> SearchQueryResponse:
        logging.info(f"[INFO][retrieval_service.py][retrieve] Executing hybrid retrieval for query: '{request.query}'")
        try:
            query_embedding = self._embed_query(request.query)

            dense_results = self._retrieval_repository.search_dense_vector(
                query_embedding = query_embedding,
                fetch_k = self._fetch_k,
                policy_id = request.policy_id
            )

            sparse_results = self._retrieval_repository.search_sparse_text(
                query_text = request.query,
                fetch_k = self._fetch_k,
                policy_id = request.policy_id
            )

            fused_candidates = self._reciprocal_rank_fusion(dense_results, sparse_results)
            reranked_results = self._rerank_candidates(request.query, fused_candidates)

            final_results = reranked_results[:self._top_k]

            response = SearchQueryResponse(
                query = request.query,
                results = final_results
            )
            return response
        except Exception as e:
            logging.error(f"[ERROR][retrieval_service.py][retrieve] Failed hybrid retrieval. Error: {e}")
            raise e

    def _embed_query(self, query: str) -> List[float]:
        logging.info(f"[INFO][retrieval_service.py][_embed_query] Generating embedding for query using {self._embedding_model}.")
        try:
            response = self._openai_client.embeddings.create(
                input = query,
                model = self._embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"[ERROR][retrieval_service.py][_embed_query] Query embedding failed. Error: {e}")
            raise e

    def _reciprocal_rank_fusion(self, dense_results: List[SearchResultChunk], sparse_results: List[SearchResultChunk], rrf_k: int = 60) -> List[SearchResultChunk]: 
        candidates_map: Dict[str, SearchResultChunk] = {}
        rrf_scores_map: Dict[str, float] = {}

        for rank, chunk in enumerate(dense_results, start = 1):
            chunk_key = f"{chunk.policy_id}_{chunk.chunk_index}"
            candidates_map[chunk_key] = chunk
            rrf_score = 1.0 / (rrf_k + rank)
            rrf_scores_map[chunk_key] = rrf_scores_map.get(chunk_key, 0.0) + rrf_score

        for rank, chunk in enumerate(sparse_results, start = 1):
            chunk_key = f"{chunk.policy_id}_{chunk.chunk_index}"
            if chunk_key not in candidates_map:
                candidates_map[chunk_key] = chunk
            else:
                candidates_map[chunk_key].text_score = chunk.text_score

            rrf_score = 1.0 / (rrf_k + rank)
            rrf_scores_map[chunk_key] = rrf_scores_map.get(chunk_key, 0.0) + rrf_score

        fused_list: List[SearchResultChunk] = []
        for chunk_key, chunk in candidates_map.items():
            chunk.rrf_score = rrf_scores_map.get(chunk_key, 0.0)
            fused_list.append(chunk)

        fused_list.sort(key = lambda x: x.rrf_score, reverse = True)
        return fused_list

    def _rerank_candidates(self, query: str, candidates: List[SearchResultChunk]) -> List[SearchResultChunk]:
        logging.info(f"[INFO][retrieval_service.py][_rerank_candidates] Reranking {len(candidates)} candidate chunks.")
        query_words = set(query.lower().split())

        for chunk in candidates:
            content_lower = chunk.content.lower()
            content_words = set(content_lower.split())

            intersection = query_words.intersection(content_words)
            lexical_overlap = len(intersection) / float(len(query_words)) if query_words else 0.0

            header_boost = 0.0
            if chunk.metadata and chunk.metadata.section_title:
                section_lower = chunk.metadata.section_title.lower()
                if any(qw in section_lower for qw in query_words):
                    header_boost = 0.2

            combined_rerank_score = (
                (chunk.rrf_score * 10.0) +
                (chunk.vector_score * 0.4) +
                (lexical_overlap * 0.4) +
                header_boost
            )
            chunk.rerank_score = round(combined_rerank_score, 4)

        candidates.sort(key = lambda x: x.rerank_score, reverse = True)
        return candidates

